use std::sync::atomic::{AtomicU64, Ordering};

use pyo3::prelude::*;
use pyo3::types::{PyAnyMethods, PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

pub static TEMPLATE_COUNTER: AtomicU64 = AtomicU64::new(0);



pub fn make_template_name(name: Option<String>) -> String {
    match name {
        Some(n) => n,
        None => {
            let id = TEMPLATE_COUNTER.fetch_add(1, Ordering::SeqCst);
            format!("template_{id}")
        }
    }
}

pub fn py_to_json(obj: &Bound<'_, PyAny>) -> PyResult<serde_json::Value> {
    if obj.is_none() {
        return Ok(serde_json::Value::Null);
    }
    if let Ok(b) = obj.cast::<PyBool>() {
        return Ok(serde_json::Value::Bool(b.extract::<bool>()?));
    }
    if let Ok(i) = obj.cast::<PyInt>() {
        if let Ok(n) = i.extract::<i64>() {
            return Ok(serde_json::Value::Number(n.into()));
        }
        if let Ok(n) = i.extract::<u64>() {
            return Ok(serde_json::Value::Number(n.into()));
        }
        let n: f64 = i.extract()?;
        return Ok(serde_json::Number::from_f64(n)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null));
    }
    if let Ok(f) = obj.cast::<PyFloat>() {
        let n: f64 = f.extract()?;
        return Ok(serde_json::Number::from_f64(n)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null));
    }
    if let Ok(s) = obj.cast::<PyString>() {
        return Ok(serde_json::Value::String(s.to_str()?.to_owned()));
    }
    if let Ok(d) = obj.cast::<PyDict>() {
        let mut map = serde_json::Map::with_capacity(d.len());
        for (k, v) in d.iter() {
            let key: String = k.extract()?;
            map.insert(key, py_to_json(&v)?);
        }
        return Ok(serde_json::Value::Object(map));
    }
    if let Ok(list) = obj.cast::<PyList>() {
        let arr = list
            .iter()
            .map(|item| py_to_json(&item))
            .collect::<PyResult<Vec<_>>>()?;
        return Ok(serde_json::Value::Array(arr));
    }
    if let Ok(tup) = obj.cast::<PyTuple>() {
        let arr = tup
            .iter()
            .map(|item| py_to_json(&item))
            .collect::<PyResult<Vec<_>>>()?;
        return Ok(serde_json::Value::Array(arr));
    }
    Err(pyo3::exceptions::PyTypeError::new_err(format!(
        "cannot convert Python type '{}' to JSON",
        obj.get_type().qualname()?
    )))
}
