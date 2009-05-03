"""
Cutplace utility functions.
"""
import os
import platform
import random
import re
import StringIO
import token
import tokenize

from datetime import timedelta, datetime
from random import randrange

class CutplaceError(Exception):
    """
    Error detected by cutplace caused by issues in the ICD or data.
    """
    pass

def valueOr(value, noneValue):
    """
    Value or noneValue in case value is None.
    """
    if value is None:
        result = noneValue
    else:
        result = value
    return result

def listdirMatching(folder, pattern):
    """
    Name of entries in folder that match regex pattern.
    """
    assert folder is not None
    assert pattern is not None
    
    regex = re.compile(pattern)
    for entry in os.listdir(folder):
        if regex.match(entry):
            yield entry

# Most popular names in the USA according to U.S. Census Bureau, Population Division, 
# Population Analysis & Evaluation Staff from 2005-11-20. 
_MALE_NAMES = ["Aaron", "Adam", "Adrian", "Alan", "Albert", "Alberto", "Alex", "Alexander", "Alfred", "Alfredo", "Allan", "Allen", "Alvin", "Andre", "Andrew", "Andy", "Angel", "Anthony", "Antonio", "Armando", "Arnold", "Arthur", "Barry", "Ben", "Benjamin", "Bernard", "Bill", "Billy", "Bob", "Bobby", "Brad", "Bradley", "Brandon", "Brent", "Brett", "Brian", "Bruce", "Bryan", "Byron", "Calvin", "Carl", "Carlos", "Casey", "Cecil", "Chad", "Charles", "Charlie", "Chester", "Chris", "Christian", "Christopher", "Clarence", "Claude", "Clayton", "Clifford", "Clifton", "Clinton", "Clyde", "Cody", "Corey", "Cory", "Craig", "Curtis", "Dale", "Dan", "Daniel", "Danny", "Darrell", "Darren", "Darryl", "Daryl", "Dave", "David", "Dean", "Dennis", "Derek", "Derrick", "Don", "Donald", "Douglas", "Duane", "Dustin", "Dwayne", "Dwight", "Earl", "Eddie", "Edgar", "Eduardo", "Edward", "Edwin", "Elmer", "Enrique", "Eric", "Erik", "Ernest", "Eugene", "Everett", "Felix", "Fernando", "Floyd", "Francis", "Francisco", "Frank", "Franklin", "Fred", "Freddie", "Frederick", "Gabriel", "Gary", "Gene", "George", "Gerald", "Gilbert", "Glen", "Glenn", "Gordon", "Greg", "Gregory", "Guy", "Harold", "Harry", "Harvey", "Hector", "Henry", "Herbert", "Herman", "Howard", "Hugh", "Ian", "Isaac", "Ivan", "Jack", "Jacob", "Jaime", "James", "Jamie", "Jared", "Jason", "Javier", "Jay", "Jeff", "Jeffery", "Jeffrey", "Jeremy", "Jerome", "Jerry", "Jesse", "Jessie", "Jesus", "Jim", "Jimmie", "Jimmy", "Joe", "Joel", "John", "Johnnie", "Johnny", "Jon", "Jonathan", "Jordan", "Jorge", "Jose", "Joseph", "Joshua", "Juan", "Julian", "Julio", "Justin", "Karl", "Keith", "Kelly", "Ken", "Kenneth", "Kent", "Kevin", "Kirk", "Kurt", "Kyle", "Lance", "Larry", "Lawrence", "Lee", "Leo", "Leon", "Leonard", "Leroy", "Leslie", "Lester", "Lewis", "Lloyd", "Lonnie", "Louis", "Luis", "Manuel", "Marc", "Marcus", "Mario", "Marion", "Mark", "Marshall", "Martin", "Marvin", "Mathew", "Matthew", "Maurice", "Max", "Melvin", "Michael", "Micheal", "Miguel", "Mike", "Milton", "Mitchell", "Morris", "Nathan", "Nathaniel", "Neil", "Nelson", "Nicholas", "Norman", "Oscar", "Patrick", "Paul", "Pedro", "Perry", "Peter", "Philip", "Phillip", "Rafael", "Ralph", "Ramon", "Randall", "Randy", "Raul", "Ray", "Raymond", "Reginald", "Rene", "Ricardo", "Richard", "Rick", "Ricky", "Robert", "Roberto", "Rodney", "Roger", "Roland", "Ron", "Ronald", "Ronnie", "Ross", "Roy", "Ruben", "Russell", "Ryan", "Salvador", "Sam", "Samuel", "Scott", "Sean", "Sergio", "Seth", "Shane", "Shawn", "Sidney", "Stanley", "Stephen", "Steve", "Steven", "Ted", "Terrance", "Terrence", "Terry", "Theodore", "Thomas", "Tim", "Timothy", "Todd", "Tom", "Tommy", "Tony", "Tracy", "Travis", "Troy", "Tyler", "Tyrone", "Vernon", "Victor", "Vincent", "Virgil", "Wade", "Wallace", "Walter", "Warren", "Wayne", "Wesley", "Willard", "William", "Willie", "Zachary"]
_FEMALE_NAMES = ['Agnes', 'Alice', 'Alicia', 'Allison', 'Alma', 'Amanda', 'Amber', 'Amy', 'Ana', 'Andrea', 'Angela', 'Anita', 'Ann', 'Anna', 'Anne', 'Annette', 'Annie', 'April', 'Arlene', 'Ashley', 'Audrey', 'Barbara', 'Beatrice', 'Becky', 'Bernice', 'Bertha', 'Bessie', 'Beth', 'Betty', 'Beverly', 'Billie', 'Bobbie', 'Bonnie', 'Brandy', 'Brenda', 'Brittany', 'Carla', 'Carmen', 'Carol', 'Carole', 'Caroline', 'Carolyn', 'Carrie', 'Cassandra', 'Catherine', 'Cathy', 'Charlene', 'Charlotte', 'Cheryl', 'Christina', 'Christine', 'Christy', 'Cindy', 'Claire', 'Clara', 'Claudia', 'Colleen', 'Connie', 'Constance', 'Courtney', 'Crystal', 'Cynthia', 'Daisy', 'Dana', 'Danielle', 'Darlene', 'Dawn', 'Deanna', 'Debbie', 'Deborah', 'Debra', 'Delores', 'Denise', 'Diana', 'Diane', 'Dianne', 'Dolores', 'Donna', 'Dora', 'Doris', 'Dorothy', 'Edith', 'Edna', 'Eileen', 'Elaine', 'Eleanor', 'Elizabeth', 'Ella', 'Ellen', 'Elsie', 'Emily', 'Emma', 'Erica', 'Erika', 'Erin', 'Esther', 'Ethel', 'Eva', 'Evelyn', 'Felicia', 'Florence', 'Frances', 'Gail', 'Georgia', 'Geraldine', 'Gertrude', 'Gina', 'Gladys', 'Glenda', 'Gloria', 'Grace', 'Gwendolyn', 'Hazel', 'Heather', 'Heidi', 'Helen', 'Hilda', 'Holly', 'Ida', 'Irene', 'Irma', 'Jackie', 'Jacqueline', 'Jamie', 'Jane', 'Janet', 'Janice', 'Jean', 'Jeanette', 'Jeanne', 'Jennie', 'Jennifer', 'Jenny', 'Jessica', 'Jessie', 'Jill', 'Jo', 'Joan', 'Joann', 'Joanne', 'Josephine', 'Joy', 'Joyce', 'Juanita', 'Judith', 'Judy', 'Julia', 'Julie', 'June', 'Karen', 'Katherine', 'Kathleen', 'Kathryn', 'Kathy', 'Katie', 'Katrina', 'Kay', 'Kelly', 'Kim', 'Kimberly', 'Kristen', 'Kristin', 'Kristina', 'Laura', 'Lauren', 'Laurie', 'Leah', 'Lena', 'Leona', 'Leslie', 'Lillian', 'Lillie', 'Linda', 'Lisa', 'Lois', 'Loretta', 'Lori', 'Lorraine', 'Louise', 'Lucille', 'Lucy', 'Lydia', 'Lynn', 'Mabel', 'Mae', 'Marcia', 'Margaret', 'Margie', 'Maria', 'Marian', 'Marie', 'Marilyn', 'Marion', 'Marjorie', 'Marlene', 'Marsha', 'Martha', 'Mary', 'Mattie', 'Maureen', 'Maxine', 'Megan', 'Melanie', 'Melinda', 'Melissa', 'Michele', 'Michelle', 'Mildred', 'Minnie', 'Miriam', 'Misty', 'Monica', 'Myrtle', 'Nancy', 'Naomi', 'Natalie', 'Nellie', 'Nicole', 'Nina', 'Nora', 'Norma', 'Olga', 'Pamela', 'Patricia', 'Patsy', 'Paula', 'Pauline', 'Pearl', 'Peggy', 'Penny', 'Phyllis', 'Priscilla', 'Rachel', 'Ramona', 'Rebecca', 'Regina', 'Renee', 'Rhonda', 'Rita', 'Roberta', 'Robin', 'Rosa', 'Rose', 'Rosemary', 'Ruby', 'Ruth', 'Sally', 'Samantha', 'Sandra', 'Sara', 'Sarah', 'Shannon', 'Sharon', 'Sheila', 'Shelly', 'Sherri', 'Sherry', 'Shirley', 'Sonia', 'Stacey', 'Stacy', 'Stella', 'Stephanie', 'Sue', 'Susan', 'Suzanne', 'Sylvia', 'Tamara', 'Tammy', 'Tanya', 'Tara', 'Teresa', 'Terri', 'Terry', 'Thelma', 'Theresa', 'Tiffany', 'Tina', 'Toni', 'Tonya', 'Tracey', 'Tracy', 'Valerie', 'Vanessa', 'Velma', 'Vera', 'Veronica', 'Vicki', 'Vickie', 'Victoria', 'Viola', 'Violet', 'Virginia', 'Vivian', 'Wanda', 'Wendy', 'Willie', 'Wilma', 'Yolanda', 'Yvonne']
_SURNAMES = ['Adams', 'Alexander', 'Allen', 'Alvarez', 'Anderson', 'Andrews', 'Armstrong', 'Arnold', 'Austin', 'Bailey', 'Baker', 'Banks', 'Barnes', 'Barnett', 'Barrett', 'Bates', 'Beck', 'Bell', 'Bennett', 'Berry', 'Bishop', 'Black', 'Bowman', 'Boyd', 'Bradley', 'Brewer', 'Brooks', 'Brown', 'Bryant', 'Burke', 'Burns', 'Burton', 'Butler', 'Byrd', 'Caldwell', 'Campbell', 'Carlson', 'Carpenter', 'Carr', 'Carroll', 'Carter', 'Castillo', 'Castro', 'Chambers', 'Chapman', 'Chavez', 'Clark', 'Cole', 'Coleman', 'Collins', 'Cook', 'Cooper', 'Cox', 'Craig', 'Crawford', 'Cruz', 'Cunningham', 'Curtis', 'Daniels', 'Davidson', 'Davis', 'Day', 'Dean', 'Diaz', 'Dixon', 'Douglas', 'Duncan', 'Dunn', 'Edwards', 'Elliott', 'Ellis', 'Evans', 'Ferguson', 'Fernandez', 'Fields', 'Fisher', 'Fleming', 'Fletcher', 'Flores', 'Ford', 'Foster', 'Fowler', 'Fox', 'Franklin', 'Frazier', 'Freeman', 'Fuller', 'Garcia', 'Gardner', 'Garrett', 'Garza', 'George', 'Gibson', 'Gilbert', 'Gomez', 'Gonzales', 'Gonzalez', 'Gordon', 'Graham', 'Grant', 'Graves', 'Gray', 'Green', 'Greene', 'Gregory', 'Griffin', 'Gutierrez', 'Hale', 'Hall', 'Hamilton', 'Hansen', 'Hanson', 'Harper', 'Harris', 'Harrison', 'Hart', 'Harvey', 'Hawkins', 'Hayes', 'Henderson', 'Henry', 'Hernandez', 'Herrera', 'Hicks', 'Hill', 'Hoffman', 'Holland', 'Holmes', 'Holt', 'Hopkins', 'Horton', 'Howard', 'Howell', 'Hudson', 'Hughes', 'Hunt', 'Hunter', 'Jackson', 'Jacobs', 'James', 'Jenkins', 'Jennings', 'Jensen', 'Jimenez', 'Johnson', 'Johnston', 'Jones', 'Jordan', 'Kelley', 'Kelly', 'Kennedy', 'Kim', 'King', 'Knight', 'Lambert', 'Lane', 'Larson', 'Lawrence', 'Lawson', 'Lee', 'Lewis', 'Little', 'Long', 'Lopez', 'Lowe', 'Lucas', 'Lynch', 'Marshall', 'Martin', 'Martinez', 'Mason', 'Matthews', 'May', 'Mccoy', 'Mcdonald', 'Mckinney', 'Medina', 'Mendoza', 'Meyer', 'Miles', 'Miller', 'Mills', 'Mitchell', 'Montgomery', 'Moore', 'Morales', 'Moreno', 'Morgan', 'Morris', 'Morrison', 'Murphy', 'Murray', 'Myers', 'Neal', 'Nelson', 'Newman', 'Nguyen', 'Nichols', 'Obrien', 'Oliver', 'Olson', 'Ortiz', 'Owens', 'Palmer', 'Parker', 'Patterson', 'Payne', 'Pearson', 'Pena', 'Perez', 'Perkins', 'Perry', 'Peters', 'Peterson', 'Phillips', 'Pierce', 'Porter', 'Powell', 'Price', 'Ramirez', 'Ramos', 'Ray', 'Reed', 'Reid', 'Reyes', 'Reynolds', 'Rhodes', 'Rice', 'Richards', 'Richardson', 'Riley', 'Rivera', 'Roberts', 'Robertson', 'Robinson', 'Rodriguez', 'Rodriquez', 'Rogers', 'Romero', 'Rose', 'Ross', 'Ruiz', 'Russell', 'Ryan', 'Sanchez', 'Sanders', 'Schmidt', 'Scott', 'Shaw', 'Shelton', 'Silva', 'Simmons', 'Simpson', 'Sims', 'Smith', 'Snyder', 'Soto', 'Spencer', 'Stanley', 'Stephens', 'Stevens', 'Stewart', 'Stone', 'Sullivan', 'Sutton', 'Taylor', 'Terry', 'Thomas', 'Thompson', 'Torres', 'Tucker', 'Turner', 'Vargas', 'Vasquez', 'Wade', 'Wagner', 'Walker', 'Wallace', 'Walters', 'Ward', 'Warren', 'Washington', 'Watkins', 'Watson', 'Watts', 'Weaver', 'Webb', 'Welch', 'Wells', 'West', 'Wheeler', 'White', 'Williams', 'Williamson', 'Willis', 'Wilson', 'Wood', 'Woods', 'Wright', 'Young']

# Based on <http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates>
def randomDatetime(startText="1900-01-01 00:00:00", endText="2009-03-15 23:59:59"):
    """
    A Random datetime between two datetime objects.
    """
    # TODO: Improve default time range: from (now - 120 years) to now.
    timeFormat = "%Y-%m-%d %H:%M:%S"
    start = datetime.strptime(startText, timeFormat)
    end = datetime.strptime(endText, timeFormat)

    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return (start + timedelta(seconds=random_second))

def createTestDateTime(format="%Y-%m-%d %H:%M:%S"):
    somewhen = randomDatetime()
    return somewhen.strftime(format)

def createTestFirstName(isMale=True):
    if isMale:
        firstNameBase = _MALE_NAMES
    else:
        firstNameBase = _FEMALE_NAMES;
    result = random.choice(firstNameBase)
    return result

def validatedPythonName(name, value):
    """
    Validated and cleaned up `value` that represents a Python name with any whitespace removed.
    If validation fails, raise `NameError` with mentioning `name` as the name under which `value`
    is known to the user.
    """
    assert name
    assert value is not None
    
    readable = StringIO.StringIO(value.strip())
    toky = tokenize.generate_tokens(readable.readline)
    next = toky.next()
    nextType = next[0]
    result = next[1]
    if tokenize.ISEOF(nextType):
        raise NameError("%s must not be empty but was: %r" % (name, value))
    if nextType != token.NAME:
        raise NameError("%s must contain only ASCII letters, digits and underscore (_) but is: %r"
                         % (name, value))
    secondToken = toky.next()
    secondTokenType = secondToken[0]
    if not tokenize.ISEOF(secondTokenType):
        raise NameError("%s must be a single word, but after %r there also is %r" % (name, result, secondToken[1]))
    return result

def createTestSurname():
    result = random.choice(_SURNAMES)
    return result

def createTestName(isMale=True):
    result = "%s %s" % (createTestFirstName(isMale), createTestSurname())
    return result

def camelized(key, firstIsLower=False):
    """
    Camelized name of possibly multiple words separated by blanks that can be used for variables.
    """
    assert key is not None
    assert key == key.strip(), "key must be trimmed"
    result = ""
    for part in key.split():
        result += part[0].upper() + part[1:].lower() 
    if firstIsLower and result:
        result = result[0].lower() + result[1:]
    return result

def platformVersion():
    macVersion = platform.mac_ver()
    if (macVersion[0]):
        result = "Mac OS %s (%s)" % (macVersion[0], macVersion[2])
    else:
        result = platform.platform()
    return result
        
def pythonVersion():
        return platform.python_version()
