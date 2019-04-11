# Ipmininet tests
The [pytest](https://docs.pytest.org/en/latest/index.html) framework is used
for the testsuite and are [integrated within
setuptools](https://docs.pytest.org/en/latest/goodpractices.html#integrating-with-setuptools-python-setup-py-test-pytest-runner).
Currently the suite has end-to-end tests that check if the daemons work as
expected. Therefore, the tests require an operating environment, i.e.  daemons
have to be installed and must be in PATH. 

## Run testsuite
To run the whole testsuite go the top level directory and run:

```
sudo python setup.py test
```

You can also run a single test by passing options to pytest:

```
python setup.py test --addopts "ipmininet/tests/test_sshd.py --fulltrace"
```
