//  GAMBIT: Global and Modular BSM Inference Tool
//  *********************************************
///  \file
///
///  Python interface for ScannerBit
///
///  *********************************************
///
///  Authors (add name and date if you modify):
///
///  \author Ben Farmer
///          (ben.farmer@gmail.com)
///  \date 2017 Nov
///
///  *********************************************

#include <iostream>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "gambit/ScannerBit/ScannerBit_CAPI.h"

namespace py = pybind11;

void py_hello_world()
{
   // Call library function
   //hello_world();
   std::cout << "hello!" <<std::endl;
} 

// Should probably encapsulate this into an object or something
py::object user_pyfunc; // Global variable defining the users chosen Python likelihood function

/// Wrapper for user-supplied likelihood function from Python
double wrapper_func(const std::unordered_map<std::string, double>& pars) 
{
   // Move the input parameters into a Python dictionary for access in the user's Python function
   //std::cout << "Parameter values:" << std::endl;
   py::dict params; 
   for (std::unordered_map<std::string, double>::const_iterator it = pars.begin(); it != pars.end(); ++it)
   {
     params[py::cast(it->first)] = py::cast(it->second);
   }
 
   // Call user-defined Python likelihood function and convert result to a double
   py::object pyr = user_pyfunc(params);
   double r = pyr.cast<double>();
   //std::cout << "result: " << r << std::endl;

   return r; // Rubbish for now, just see if it works 
}

/// Error-tolerant getter for dictionary items
py::object get_dict_or_empty(const py::dict& d, const std::string& key)
{
  py::object get = d.attr("get"); // Extract "get" method for this dictionary
  py::object out = get(py::str(key),py::dict()); // Call get method with python string argument. Return empty dict if no matching key.
  return out;
}

/// Wrapper for pybind11 cast that modifies the error message
template<class T>
T info_cast(const py::handle& in, const std::string& msg)
{
   T out;
   try 
   {
       out = py::cast<T>(in);
   }
   catch (const py::cast_error& e)
   {
      std::ostringstream err;
	  err<<msg<<". Original message was: "<<e.what();
	  throw py::cast_error(err.str());
   }
   return out;
}

/// Check if a python type can be mapped to a C++ type (under our rules)
bool allowed_pytype(const py::handle& value)
{
    bool out = false;
    if(  py::isinstance<py::none>(value)
      or py::str(value).is(py::str(Py_True)) 
      or py::str(value).is(py::str(Py_False)) 
      or py::isinstance<py::int_>(value)  
      or py::isinstance<py::float_>(value)    
      or py::isinstance<py::str>(value) )
    { 
        out = true;
    }
    return out;
}

/// Convert simple python type to YAML node
YAML::Node pytype_to_yaml(const py::handle& value, const std::string& err)
{
    YAML::Node node_out;
    if     (py::isinstance<py::none>(value))      node_out = YAML::Load(""); // Should give a Null node (YAML::NodeType::Null)
    else if(py::str(value).is(py::str(Py_True)))  node_out = "true";
    else if(py::str(value).is(py::str(Py_False))) node_out = "false";
    else if(py::isinstance<py::int_>(value))      node_out = info_cast<int>(value,err); 
    else if(py::isinstance<py::float_>(value))    node_out = info_cast<double>(value,err);
    else if(py::isinstance<py::str>(value))       node_out = info_cast<std::string>(value,err);
    else
    {
        // Not an allowed simple python type
        // First, get the type name
        std::string type = py::str(value.get_type());
        std::ostringstream msg;
        msg<<"Unhandled type encountered while converting python dictionary to YAML format. Saw Python type '"<<type<<"', which is not currently handled by this interface. Further info: "<<err;
        throw std::invalid_argument(msg.str()); // pybind11 should convert this into something that Python can catch (ValueError I think)
    }
    return node_out;
}

/// Convert python list/tuple of constant type to YAML node
YAML::Node pylist_to_yaml(const py::handle& value, const std::string& err)
{
   YAML::Node node_out;
   py::handle pytype;
   auto iter = py::iter(value);
   bool first = true;
   while (iter != py::iterator::sentinel())
   {
       if(first) 
       {
          pytype = iter->get_type();
          first = false;
       }
       else if(not py::isinstance(*iter,pytype))
       {
           // Mixed types!
           std::ostringstream msg;
           msg<<"Mixed types detected while converting a python iterable into YAML! (prior elements were "<<py::str(pytype)<<", this element was "<<py::str(iter->get_type())<<"). This is not currently handled by this interface. Further info: "<<err;
           throw std::invalid_argument(msg.str());
       }
       ++iter;
   }

   if(first)
   {
      // List was empty! Not sure how to return an empty list. I guess we can return an empty vector?
      // Maybe better to just leave empty node.
   }
   else
   {
      // Ok types are consistent, but are they allowed?
      py::list list = info_cast<py::list>(value,err);
      if(allowed_pytype(list[0]))
      {
          // TODO: Actually bools are a pain. Leave those out for now. Same for NoneTypes
          //if     (py::str(value[0]).is(py::str(Py_True)))  node_out[key] = "true";
          //else if(py::str(value[0]).is(py::str(Py_False))) node_out[key] = "false";
          if     (py::isinstance<py::int_>(list[0]))   node_out = info_cast<std::vector<int>>(value,err); 
          else if(py::isinstance<py::float_>(list[0])) node_out = info_cast<std::vector<double>>(value,err);
          else if(py::isinstance<py::str>(list[0]))    node_out = info_cast<std::vector<std::string>>(value,err);
          else
          {
              std::ostringstream msg;
              msg<<"Unhandled type detected while converting a python iterable into YAML! (type was "<<py::str(pytype)<<"). This is not currently handled by this interface. However, this should have been caught earlier so this is a bug. Further info: "<<err;
              throw std::invalid_argument(msg.str()); 
          }
      }
      else
      {
          std::ostringstream msg;
          msg<<"Unhandled type detected while converting a python iterable into YAML! (type was "<<py::str(pytype)<<"). This is not currently handled by this interface. Further info: "<<err;
          throw std::invalid_argument(msg.str()); 
      }
   }
   return node_out;
}

/// General-purpose function to convert a set of nested Python dictionaries and
/// their contents into YAML format.
/// Restrictions: 
///  - all keys assumed to be strings
///  - values must be one of the following Python types:
///    - bool, int, float
///    - string
///    - list/tuple of numeric types or strings (not mixed!)
///    - another dictionary
YAML::Node pydict_to_yaml(const py::dict& d, const std::string& dict_level = "/")
{
    YAML::Node node_out;
    for (auto item: d)
    {
        std::string key = py::cast<py::str>(item.first);
        std::string current_dict_level = dict_level+"/"+key;    

        /// Message for casting errors
        std::ostringstream err;
	    err<<"Pybind11 failed to cast an element of the settings dictionary to the required C++ type. Error occurred in the settings dictionary at location '"<<current_dict_level<<"'";
        /// Figure out what kind of Python object the 'value' is  
        /// and cast it to an appropriate C++ type 
        /// (pybind handles the converions for us)
        py::handle value = item.second;
        if(allowed_pytype(value)) // This handles all the allowed simple type conversions
        {
           node_out[key] = pytype_to_yaml(value,err.str());
        }
        else if(py::isinstance<py::tuple>(value) or py::isinstance<py::list>(value))
        {
           // Need to check type of list/tuple elements
           // We can only convert them easily if they are all the same type, which
           // is all we want to handle anyway.
           node_out[key] = pylist_to_yaml(value,err.str());
           node_out[key].SetStyle(YAML::EmitterStyle::Flow); // Just for nice in-line output during debugging 
        }
        else if(py::isinstance<py::dict>(value))
        {
           // "We need to go deeper"
           node_out[key] = pydict_to_yaml(info_cast<py::dict>(value,err.str()),current_dict_level);
        }
        else
        {
           // Unhandled type
           // First, get the type name
           std::string type = py::str(value.get_type());
           std::ostringstream err;
           err<<"Unhandled type encountered while converting python dictionary to YAML format. At dictionary location '"
              <<current_dict_level<<"' saw Python type '"<<type<<"', which is not currently handled by this interface";
           throw std::invalid_argument(err.str()); // pybind11 should convert this into something that Python can catch (ValueError I think)
        }
    }
    return node_out;
}

void py_run_scan(const py::dict& d, const py::object& f)
{
   // Set user-defined Python function for callbacks
   user_pyfunc = f;   

   // Need to read the supplied Python dictionary and
   // convert it into a YAML node that ScannerBitCAPI
   // can understand.
   // We handle missing options, defaults, stucture, etc
   // on the Python side. Here it is assumed that d is
   // the complete set of options required by
   // ScannerBit.
   YAML::Node root = pydict_to_yaml(d);  

   // Check what we have cooked up here
   std::cout << "Constructed YAML node:" << std::endl;
   std::cout << root << std::endl;

   // Call library function
   run_scan(root,&wrapper_func,false); // Last argument tells ScannerBit not to INIT_MPI. Will be done in Python.
}

void py_run_scan_from_file(const char yaml_file[], const py::object& f)
{
   // Set user-defined Python function for callbacks
   user_pyfunc = f;   

   // Call library function
   run_scan_from_file(yaml_file,&wrapper_func,false); // Last argument tells ScannerBit not to INIT_MPI. Will be done in Python.
}

PYBIND11_MODULE(_interface, m) {
    m.doc() = "doc string goes here";
    m.attr("__name__") = "pyscannerbit._interface";
    m.def("hello", &py_hello_world);
    m.def("run_scan", &py_run_scan);
}
