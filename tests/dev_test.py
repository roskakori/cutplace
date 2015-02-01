"""
Development tool and utility functions for testing and test data generation.
"""
# Copyright (C) 2009-2015 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import fnmatch
import logging
import os
import random
import sys
from datetime import timedelta, datetime
from random import randrange

import six

_log = logging.getLogger("cutplace.tests")

# Most popular names in the USA according to U.S. Census Bureau, Population Division,
# Population Analysis & Evaluation Staff from 2005-11-20.
_MALE_NAMES = [
    "Aaron", "Adam", "Adrian", "Alan", "Albert", "Alberto", "Alex", "Alexander", "Alfred", "Alfredo", "Allan", "Allen",
    "Alvin", "Andre", "Andrew", "Andy", "Angel", "Anthony", "Antonio", "Armando", "Arnold", "Arthur", "Barry", "Ben",
    "Benjamin", "Bernard", "Bill", "Billy", "Bob", "Bobby", "Brad", "Bradley", "Brandon", "Brent", "Brett", "Brian",
    "Bruce", "Bryan", "Byron", "Calvin", "Carl", "Carlos", "Casey", "Cecil", "Chad", "Charles", "Charlie", "Chester",
    "Chris", "Christian", "Christopher", "Clarence", "Claude", "Clayton", "Clifford", "Clifton", "Clinton", "Clyde",
    "Cody", "Corey", "Cory", "Craig", "Curtis", "Dale", "Dan", "Daniel", "Danny", "Darrell", "Darren", "Darryl",
    "Daryl", "Dave", "David", "Dean", "Dennis", "Derek", "Derrick", "Don", "Donald", "Douglas", "Duane", "Dustin",
    "Dwayne", "Dwight", "Earl", "Eddie", "Edgar", "Eduardo", "Edward", "Edwin", "Elmer", "Enrique", "Eric", "Erik",
    "Ernest", "Eugene", "Everett", "Felix", "Fernando", "Floyd", "Francis", "Francisco", "Frank", "Franklin", "Fred",
    "Freddie", "Frederick", "Gabriel", "Gary", "Gene", "George", "Gerald", "Gilbert", "Glen", "Glenn", "Gordon", "Greg",
    "Gregory", "Guy", "Harold", "Harry", "Harvey", "Hector", "Henry", "Herbert", "Herman", "Howard", "Hugh", "Ian",
    "Isaac", "Ivan", "Jack", "Jacob", "Jaime", "James", "Jamie", "Jared", "Jason", "Javier", "Jay", "Jeff", "Jeffery",
    "Jeffrey", "Jeremy", "Jerome", "Jerry", "Jesse", "Jessie", "Jesus", "Jim", "Jimmie", "Jimmy", "Joe", "Joel", "John",
    "Johnnie", "Johnny", "Jon", "Jonathan", "Jordan", "Jorge", "Jose", "Joseph", "Joshua", "Juan", "Julian", "Julio",
    "Justin", "Karl", "Keith", "Kelly", "Ken", "Kenneth", "Kent", "Kevin", "Kirk", "Kurt", "Kyle", "Lance", "Larry",
    "Lawrence", "Lee", "Leo", "Leon", "Leonard", "Leroy", "Leslie", "Lester", "Lewis", "Lloyd", "Lonnie", "Louis",
    "Luis", "Manuel", "Marc", "Marcus", "Mario", "Marion", "Mark", "Marshall", "Martin", "Marvin", "Mathew", "Matthew",
    "Maurice", "Max", "Melvin", "Michael", "Micheal", "Miguel", "Mike", "Milton", "Mitchell", "Morris", "Nathan",
    "Nathaniel", "Neil", "Nelson", "Nicholas", "Norman", "Oscar", "Patrick", "Paul", "Pedro", "Perry", "Peter",
    "Philip", "Phillip", "Rafael", "Ralph", "Ramon", "Randall", "Randy", "Raul", "Ray", "Raymond", "Reginald", "Rene",
    "Ricardo", "Richard", "Rick", "Ricky", "Robert", "Roberto", "Rodney", "Roger", "Roland", "Ron", "Ronald", "Ronnie",
    "Ross", "Roy", "Ruben", "Russell", "Ryan", "Salvador", "Sam", "Samuel", "Scott", "Sean", "Sergio", "Seth", "Shane",
    "Shawn", "Sidney", "Stanley", "Stephen", "Steve", "Steven", "Ted", "Terrance", "Terrence", "Terry", "Theodore",
    "Thomas", "Tim", "Timothy", "Todd", "Tom", "Tommy", "Tony", "Tracy", "Travis", "Troy", "Tyler", "Tyrone", "Vernon",
    "Victor", "Vincent", "Virgil", "Wade", "Wallace", "Walter", "Warren", "Wayne", "Wesley", "Willard", "William",
    "Willie", "Zachary"
]
_FEMALE_NAMES = [
    'Agnes', 'Alice', 'Alicia', 'Allison', 'Alma', 'Amanda', 'Amber', 'Amy', 'Ana', 'Andrea', 'Angela', 'Anita', 'Ann',
    'Anna', 'Anne', 'Annette', 'Annie', 'April', 'Arlene', 'Ashley', 'Audrey', 'Barbara', 'Beatrice', 'Becky',
    'Bernice', 'Bertha', 'Bessie', 'Beth', 'Betty', 'Beverly', 'Billie', 'Bobbie', 'Bonnie', 'Brandy', 'Brenda',
    'Brittany', 'Carla', 'Carmen', 'Carol', 'Carole', 'Caroline', 'Carolyn', 'Carrie', 'Cassandra', 'Catherine',
    'Cathy', 'Charlene', 'Charlotte', 'Cheryl', 'Christina', 'Christine', 'Christy', 'Cindy', 'Claire', 'Clara',
    'Claudia', 'Colleen', 'Connie', 'Constance', 'Courtney', 'Crystal', 'Cynthia', 'Daisy', 'Dana', 'Danielle',
    'Darlene', 'Dawn', 'Deanna', 'Debbie', 'Deborah', 'Debra', 'Delores', 'Denise', 'Diana', 'Diane', 'Dianne',
    'Dolores', 'Donna', 'Dora', 'Doris', 'Dorothy', 'Edith', 'Edna', 'Eileen', 'Elaine', 'Eleanor', 'Elizabeth', 'Ella',
    'Ellen', 'Elsie', 'Emily', 'Emma', 'Erica', 'Erika', 'Erin', 'Esther', 'Ethel', 'Eva', 'Evelyn', 'Felicia',
    'Florence', 'Frances', 'Gail', 'Georgia', 'Geraldine', 'Gertrude', 'Gina', 'Gladys', 'Glenda', 'Gloria', 'Grace',
    'Gwendolyn', 'Hazel', 'Heather', 'Heidi', 'Helen', 'Hilda', 'Holly', 'Ida', 'Irene', 'Irma', 'Jackie', 'Jacqueline',
    'Jamie', 'Jane', 'Janet', 'Janice', 'Jean', 'Jeanette', 'Jeanne', 'Jennie', 'Jennifer', 'Jenny', 'Jessica',
    'Jessie', 'Jill', 'Jo', 'Joan', 'Joann', 'Joanne', 'Josephine', 'Joy', 'Joyce', 'Juanita', 'Judith', 'Judy',
    'Julia', 'Julie', 'June', 'Karen', 'Katherine', 'Kathleen', 'Kathryn', 'Kathy', 'Katie', 'Katrina', 'Kay', 'Kelly',
    'Kim', 'Kimberly', 'Kristen', 'Kristin', 'Kristina', 'Laura', 'Lauren', 'Laurie', 'Leah', 'Lena', 'Leona', 'Leslie',
    'Lillian', 'Lillie', 'Linda', 'Lisa', 'Lois', 'Loretta', 'Lori', 'Lorraine', 'Louise', 'Lucille', 'Lucy', 'Lydia',
    'Lynn', 'Mabel', 'Mae', 'Marcia', 'Margaret', 'Margie', 'Maria', 'Marian', 'Marie', 'Marilyn', 'Marion', 'Marjorie',
    'Marlene', 'Marsha', 'Martha', 'Mary', 'Mattie', 'Maureen', 'Maxine', 'Megan', 'Melanie', 'Melinda', 'Melissa',
    'Michele', 'Michelle', 'Mildred', 'Minnie', 'Miriam', 'Misty', 'Monica', 'Myrtle', 'Nancy', 'Naomi', 'Natalie',
    'Nellie', 'Nicole', 'Nina', 'Nora', 'Norma', 'Olga', 'Pamela', 'Patricia', 'Patsy', 'Paula', 'Pauline', 'Pearl',
    'Peggy', 'Penny', 'Phyllis', 'Priscilla', 'Rachel', 'Ramona', 'Rebecca', 'Regina', 'Renee', 'Rhonda', 'Rita',
    'Roberta', 'Robin', 'Rosa', 'Rose', 'Rosemary', 'Ruby', 'Ruth', 'Sally', 'Samantha', 'Sandra', 'Sara', 'Sarah',
    'Shannon', 'Sharon', 'Sheila', 'Shelly', 'Sherri', 'Sherry', 'Shirley', 'Sonia', 'Stacey', 'Stacy', 'Stella',
    'Stephanie', 'Sue', 'Susan', 'Suzanne', 'Sylvia', 'Tamara', 'Tammy', 'Tanya', 'Tara', 'Teresa', 'Terri', 'Terry',
    'Thelma', 'Theresa', 'Tiffany', 'Tina', 'Toni', 'Tonya', 'Tracey', 'Tracy', 'Valerie', 'Vanessa', 'Velma', 'Vera',
    'Veronica', 'Vicki', 'Vickie', 'Victoria', 'Viola', 'Violet', 'Virginia', 'Vivian', 'Wanda', 'Wendy', 'Willie',
    'Wilma', 'Yolanda', 'Yvonne'
]
_SURNAMES = [
    'Adams', 'Alexander', 'Allen', 'Alvarez', 'Anderson', 'Andrews', 'Armstrong', 'Arnold', 'Austin', 'Bailey', 'Baker',
    'Banks', 'Barnes', 'Barnett', 'Barrett', 'Bates', 'Beck', 'Bell', 'Bennett', 'Berry', 'Bishop', 'Black', 'Bowman',
    'Boyd', 'Bradley', 'Brewer', 'Brooks', 'Brown', 'Bryant', 'Burke', 'Burns', 'Burton', 'Butler', 'Byrd', 'Caldwell',
    'Campbell', 'Carlson', 'Carpenter', 'Carr', 'Carroll', 'Carter', 'Castillo', 'Castro', 'Chambers', 'Chapman',
    'Chavez', 'Clark', 'Cole', 'Coleman', 'Collins', 'Cook', 'Cooper', 'Cox', 'Craig', 'Crawford', 'Cruz', 'Cunningham',
    'Curtis', 'Daniels', 'Davidson', 'Davis', 'Day', 'Dean', 'Diaz', 'Dixon', 'Douglas', 'Duncan', 'Dunn', 'Edwards',
    'Elliott', 'Ellis', 'Evans', 'Ferguson', 'Fernandez', 'Fields', 'Fisher', 'Fleming', 'Fletcher', 'Flores', 'Ford',
    'Foster', 'Fowler', 'Fox', 'Franklin', 'Frazier', 'Freeman', 'Fuller', 'Garcia', 'Gardner', 'Garrett', 'Garza',
    'George', 'Gibson', 'Gilbert', 'Gomez', 'Gonzales', 'Gonzalez', 'Gordon', 'Graham', 'Grant', 'Graves', 'Gray',
    'Green', 'Greene', 'Gregory', 'Griffin', 'Gutierrez', 'Hale', 'Hall', 'Hamilton', 'Hansen', 'Hanson', 'Harper',
    'Harris', 'Harrison', 'Hart', 'Harvey', 'Hawkins', 'Hayes', 'Henderson', 'Henry', 'Hernandez', 'Herrera', 'Hicks',
    'Hill', 'Hoffman', 'Holland', 'Holmes', 'Holt', 'Hopkins', 'Horton', 'Howard', 'Howell', 'Hudson', 'Hughes', 'Hunt',
    'Hunter', 'Jackson', 'Jacobs', 'James', 'Jenkins', 'Jennings', 'Jensen', 'Jimenez', 'Johnson', 'Johnston', 'Jones',
    'Jordan', 'Kelley', 'Kelly', 'Kennedy', 'Kim', 'King', 'Knight', 'Lambert', 'Lane', 'Larson', 'Lawrence', 'Lawson',
    'Lee', 'Lewis', 'Little', 'Long', 'Lopez', 'Lowe', 'Lucas', 'Lynch', 'Marshall', 'Martin', 'Martinez', 'Mason',
    'Matthews', 'May', 'Mccoy', 'Mcdonald', 'Mckinney', 'Medina', 'Mendoza', 'Meyer', 'Miles', 'Miller', 'Mills',
    'Mitchell', 'Montgomery', 'Moore', 'Morales', 'Moreno', 'Morgan', 'Morris', 'Morrison', 'Murphy', 'Murray', 'Myers',
    'Neal', 'Nelson', 'Newman', 'Nguyen', 'Nichols', 'Obrien', 'Oliver', 'Olson', 'Ortiz', 'Owens', 'Palmer', 'Parker',
    'Patterson', 'Payne', 'Pearson', 'Pena', 'Perez', 'Perkins', 'Perry', 'Peters', 'Peterson', 'Phillips', 'Pierce',
    'Porter', 'Powell', 'Price', 'Ramirez', 'Ramos', 'Ray', 'Reed', 'Reid', 'Reyes', 'Reynolds', 'Rhodes', 'Rice',
    'Richards', 'Richardson', 'Riley', 'Rivera', 'Roberts', 'Robertson', 'Robinson', 'Rodriguez', 'Rodriquez', 'Rogers',
    'Romero', 'Rose', 'Ross', 'Ruiz', 'Russell', 'Ryan', 'Sanchez', 'Sanders', 'Schmidt', 'Scott', 'Shaw', 'Shelton',
    'Silva', 'Simmons', 'Simpson', 'Sims', 'Smith', 'Snyder', 'Soto', 'Spencer', 'Stanley', 'Stephens', 'Stevens',
    'Stewart', 'Stone', 'Sullivan', 'Sutton', 'Taylor', 'Terry', 'Thomas', 'Thompson', 'Torres', 'Tucker', 'Turner',
    'Vargas', 'Vasquez', 'Wade', 'Wagner', 'Walker', 'Wallace', 'Walters', 'Ward', 'Warren', 'Washington', 'Watkins',
    'Watson', 'Watts', 'Weaver', 'Webb', 'Welch', 'Wells', 'West', 'Wheeler', 'White', 'Williams', 'Williamson',
    'Willis', 'Wilson', 'Wood', 'Woods', 'Wright', 'Young'
]


def _random_datetime(start_text="1900-01-01 00:00:00", end_text="2009-03-15 23:59:59"):
    """
    A Random datetime between two datetime objects.

    Based on <http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates>.
    """
    # TODO: Improve default time range: from (now - 120 years) to now.
    timeFormat = "%Y-%m-%d %H:%M:%S"
    start = datetime.strptime(start_text, timeFormat)
    end = datetime.strptime(end_text, timeFormat)

    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return (start + timedelta(seconds=random_second))


def random_datetime(time_format="%Y-%m-%d %H:%M:%S"):
    sometimes = _random_datetime()
    return six.text_type(sometimes.strftime(time_format))


def random_first_name(is_male=True):
    if is_male:
        first_names_pool = _MALE_NAMES
    else:
        first_names_pool = _FEMALE_NAMES
    result = random.choice(first_names_pool)
    return result


def random_surname():
    result = random.choice(_SURNAMES)
    return result


def random_name(is_male=True):
    result = "%s %s" % (random_first_name(is_male), random_surname())
    return result


def path_to_test_folder(folder):
    """
    Path to sub folder `folder` in 'tests' folder.
    """
    assert folder

    # Attempt to find `folder` in "tests" folder based from current folder.
    test_folder = os.path.join(os.getcwd(), "tests")
    if not os.path.exists(test_folder) and (len(sys.argv) == 2):
        # Try the folder specified in the one and only command line option.
        # TODO: Make the base folder a property setable from outside.
        test_folder = os.path.join(sys.argv[1], "tests")
    if not os.path.exists(test_folder):
        base_path = os.getcwd()
        test_folder_found = False
        while not test_folder_found and base_path:
            base_path = os.path.split(base_path)[0]
            test_folder = os.path.join(base_path, "tests")
            test_folder_found = os.path.exists(test_folder)
    if not os.path.exists(test_folder):
        raise IOError("cannot find test folder: test must run from project folder or project folder must be passed as command line option; currently attempting to find test folder in: %r" % test_folder)
    result = os.path.join(test_folder, folder)
    return result


def path_to_test_file(folder, file_name):
    """
    Path of file `file_name` in `folder` located in 'tests' folder.
    """
    assert folder
    assert file_name

    result = os.path.join(path_to_test_folder(folder), file_name)
    return result


def path_to_test_data(file_name):
    """
    Path to test file `file_name` in 'tests/data' folder.
    """
    assert file_name
    return path_to_test_file("data", file_name)


def path_to_test_result(file_name):
    """
    Path to test file `file_name` in 'tests/result' folder.
    """
    assert file_name
    return path_to_test_file("results", file_name)


def path_to_test_cid(cid_file_name):
    """
    Path to test CID `cid_file_name` which has to be located in 'tests/input/cids'.
    """
    assert cid_file_name
    return path_to_test_file(os.path.join("data", "cids"), cid_file_name)


def path_to_test_plugins():
    """
    Path to folder containing test plugins.
    """
    return path_to_test_folder("data")


def create_test_customer_row(customer_id):
    branch_id = random.choice(['38000', '38053', '38111'])
    gender = random.choice(['female', 'male'])
    first_name = random_first_name(gender == 'male')
    surname = random_surname()
    if random.randint(0, 100) == 0:
        gender = "unknown"
    date_of_birth = random_datetime("%d.%m.%Y")
    return [branch_id, six.text_type(customer_id), first_name, surname, gender, date_of_birth]


def assert_fnmatches(test_case, actual_value, expected_pattern):
    assert test_case is not None
    assert expected_pattern is not None

    test_case.assertNotEqual(None, actual_value)
    if not fnmatch.fnmatch(actual_value, expected_pattern):
        test_case.fail('%r must match pattern %r' % (actual_value, expected_pattern))


def unified_newlines(text):
    """
    Same as ``text`` but with newline sequences unified to ``'\n'``.
    """
    assert text is not None
    return text.replace('\r\n', '\n').replace('\r', '\n')
