# FactorialHR work time verification

This script verifies attendances whether they comply with german law. In particular, the following rules are verified:
- Whether the work time is longer than 6 hours without a break of 30 min
- Whether the work time is longer than 9 hours without a break of 45 min
- Whether the work time is longer than 10 hours without a break of 11 hours

It also provides a way to fetch the attendances of all employees from [FactorialHR](https://apidoc.factorialhr.com/docs) using a [company api-key](https://help.factorialhr.com/how-to-create-api-keys-in-factorial). Its then printed nicely to the console using [tabulate](https://pypi.org/project/tabulate/).
## Disclaimer

I do not guarantee that this package complies with german law all the time. Changes may occur anytime. Use at your own risk.

## Usage

Install the tool with `pip install fwtv` and then use it by providing an iso-formatted start date and an iso-formatted end date which represent the time interval that will be verified.

E.g.
```
factorial-wtv 2023-01-01 2023-02-01 <api-key>
```
will verify all attendances of all employees in january 2023.

### Preconditions

Preconditions errors are syntactical errors like an attendance that starts and end and the same time, or if a `clock_in` or `clock_out` parameter is missing.

## Contributing

Feel free to contribute! Please fork this repository, install the development dependencies with `pip install -e ".[dev]"` and create pull request.