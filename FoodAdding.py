from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Course, FoodItem, Base

engine = create_engine('postgresql://catalog:password@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Establishing Meals
course1 = Course(name="Breakfast")
session.add(course1)
session.commit()

food1 = FoodItem(name="Pancakes",
                 description="A fluffy circular sweet bread.",
                 course=course1)

session.add(food1)
session.commit()

course2 = Course(name="Lunch")
session.add(course2)
session.commit()

food2 = FoodItem(name="Chicken sandwich",
                 description="chicken with bread, lettuce, and tomato",
                 course=course2)
session.add(food2)
session.commit()

course3 = Course(name="Dinner")
session.add(course3)
session.commit()
food3 = FoodItem(name="Mac and Cheese",
                 description="Pasta with 4 types of cheeses",
                 course=course3)
session.add(food2)
session.commit()

print "added menu items to lunch!"
