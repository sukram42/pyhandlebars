use pyo3::prelude::*;
use pyo3::types::PyAnyMethods;

use handlebars::{
    Context, Handlebars, Helper, HelperDef, HelperResult, Output, RenderContext, RenderError,
    RenderErrorReason,
};

mod utils;
use utils::{make_template_name, py_to_json};

pyo3::create_exception!(
    pyhandlebars,
    PyHandlebarsError,
    pyo3::exceptions::PyException
);
pyo3::create_exception!(pyhandlebars, TemplateParseError, PyHandlebarsError);
pyo3::create_exception!(pyhandlebars, FormatError, PyHandlebarsError);
pyo3::create_exception!(pyhandlebars, HelperError, PyHandlebarsError);

struct PyHelper(Py<PyAny>);

// SAFETY: Py<PyAny> is Send. We never access it without holding the GIL via Python::attach.
unsafe impl Sync for PyHelper {}

impl HelperDef for PyHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        _: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        _: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> HelperResult {
        let result = Python::attach(|py| -> PyResult<String> {
            let json_mod = py.import("json")?;

            let args: Vec<Py<PyAny>> = h
                .params()
                .iter()
                .map(|p| {
                    let s = serde_json::to_string(p.value())
                        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
                    json_mod.call_method1("loads", (s,)).map(|r| r.into())
                })
                .collect::<PyResult<_>>()?;

            let data_str = serde_json::to_string(ctx.data())
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let data_py: Py<PyAny> = json_mod.call_method1("loads", (data_str,))?.into();

            let ret = self.0.call1(py, (args, data_py))?;
            if let Ok(s) = ret.extract::<String>(py) {
                Ok(s)
            } else {
                json_mod.call_method1("dumps", (ret,))?.extract::<String>()
            }
        });

        match result {
            Ok(s) => {
                out.write(&s)?;
                Ok(())
            }
            Err(e) => Err(RenderErrorReason::Other(format!("\x00helper\x00{}", e)).into()),
        }
    }
}

#[pyclass]
struct PyHandlebars {
    client: Handlebars<'static>,
}

#[pymethods]
impl PyHandlebars {
    #[new]
    #[pyo3(signature = (*, dev_mode=false, strict_mode=false))]
    fn new(dev_mode: bool, strict_mode: bool) -> Self {
        let mut client = Handlebars::new();
        client.set_strict_mode(strict_mode);
        client.set_dev_mode(dev_mode);
        PyHandlebars { client }
    }

    fn register_helper(&mut self, name: &str, func: Py<PyAny>) {
        self.client.register_helper(name, Box::new(PyHelper(func)));
    }
}

fn render_error_to_py(e: RenderError) -> PyErr {
    let msg = e.to_string();
    if let Some(pos) = msg.find("\x00helper\x00") {
        return HelperError::new_err(msg[pos + "\x00helper\x00".len()..].to_string());
    }
    let detail = match e.reason() {
        RenderErrorReason::MissingVariable(Some(var)) => {
            format!(
                "In the template the variable '{var}' is expected, but not provided when calling Template.format(). This error is only raised if the PyHandlebars(strict_mode=True) is set."
            )
        }
        _ => msg,
    };
    FormatError::new_err(detail)
}

#[pyclass]
struct Template {
    client: Py<PyHandlebars>,
    key: String,
}

#[pymethods]
impl Template {
    #[new]
    #[pyo3(signature = (template, *, name=None, client=None))]
    fn new(
        py: Python,
        template: &str,
        name: Option<String>,
        client: Option<Py<PyHandlebars>>,
    ) -> PyResult<Self> {
        let client = match client {
            Some(c) => c,
            None => Py::new(
                py,
                PyHandlebars {
                    client: Handlebars::new(),
                },
            )?,
        };
        let key = make_template_name(name);
        client
            .borrow_mut(py)
            .client
            .register_template_string(&key, template)
            .map_err(|e| TemplateParseError::new_err(e.to_string()))?;
        Ok(Template { client, key })
    }

    #[classmethod]
    #[pyo3(signature = (path, *, name=None, client=None))]
    fn from_file(
        _cls: &Bound<'_, pyo3::types::PyType>,
        py: Python,
        path: &Bound<'_, PyAny>,
        name: Option<String>,
        client: Option<Py<PyHandlebars>>,
    ) -> PyResult<Self> {
        let key = make_template_name(name);
        let path_str: String = path.str()?.extract()?;
        let client = match client {
            Some(c) => c,
            None => Py::new(
                py,
                PyHandlebars {
                    client: Handlebars::new(),
                },
            )?,
        };
        client
            .borrow_mut(py)
            .client
            .register_template_file(&key, &path_str)
            .map_err(|e| TemplateParseError::new_err(e.to_string()))?;
        Ok(Template { client, key })
    }

    fn format(&self, data: &Bound<'_, PyAny>) -> PyResult<String> {
        let py = data.py();

        let serializable = if data.hasattr("model_dump")? {
            data.call_method0("model_dump")?
        } else {
            data.clone()
        };

        let json_data = py_to_json(&serializable)?;

        self.client
            .borrow(py)
            .client
            .render(&self.key, &json_data)
            .map_err(render_error_to_py)
    }
}

impl Drop for Template {
    fn drop(&mut self) {
        Python::attach(|py| {
            self.client
                .borrow_mut(py)
                .client
                .unregister_template(&self.key);
        });
    }
}

#[pymodule]
fn pyhandlebars(_py: Python<'_>, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_class::<PyHandlebars>()?;
    m.add_class::<Template>()?;

    m.add("PyHandlebarsError", m.py().get_type::<PyHandlebarsError>())?;
    m.add(
        "TemplateParseError",
        m.py().get_type::<TemplateParseError>(),
    )?;
    m.add("FormatError", m.py().get_type::<FormatError>())?;
    m.add("HelperError", m.py().get_type::<HelperError>())?;

    Ok(())
}
