from django.test.simple import *

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    """
    worsk exactly as per normal test
    but only creates the test_db if it doesn't yet exist
    and does not destroy it when done
    tables are flushed and fixtures loaded between tests as per usual
    but if your schema has not changed then this saves significant amounts of time
    and speeds up the test cycle
    
    Run the unit tests for all the test labels in the provided list.
    Labels must be of the form:
     - app.TestClass.test_method
        Run a single specific test method
     - app.TestClass
        Run all the test methods in a given class
     - app
        Search for doctests and unittests in the named application.

    When looking for tests, the test runner will look in the models and
    tests modules for the application.
    
    A list of 'extra' tests may also be provided; these tests
    will be added to the test suite.
    
    Returns the number of tests that failed.
    """
    setup_test_environment()
    
    settings.DEBUG = False    
    suite = unittest.TestSuite()

    # http://code.djangoproject.com/attachment/ticket/5979/test_siteid_overwrite_r6720.patch
    settings.SITE_ID = 1

    if test_labels:
        for label in test_labels:
            if '.' in label:
                suite.addTest(build_test(label))
            else:
                app = get_app(label)
                suite.addTest(build_suite(app))
    else:
        for app in get_apps():
            suite.addTest(build_suite(app))
    
    for test in extra_tests:
        suite.addTest(test)

    from django.db.backends import creation
    old_name = settings.DATABASE_NAME
    if settings.TEST_DATABASE_NAME:
        test_database_name = settings.TEST_DATABASE_NAME
    else:
        test_database_name = creation.TEST_DATABASE_PREFIX + settings.DATABASE_NAME

    # does test db exist already ?
    from django.db import connection, DatabaseError
    settings.DATABASE_NAME = test_database_name
    try:
        cursor = connection.cursor()
    except DatabaseError, e:
        # db does not exist
        # juggling !  create_test_db switches the DATABASE_NAME to the TEST_DATABASE_NAME 
        settings.DATABASE_NAME = old_name
        connection.creation.create_test_db(verbosity, autoclobber=True)
    else:
        connection.close()

    tr = unittest.TextTestRunner(verbosity=verbosity)
    
    result = tr.run(suite)
    
    # but keep the test db
    settings.DATABASE_NAME = old_name

    teardown_test_environment()

    return len(result.failures) + len(result.errors)