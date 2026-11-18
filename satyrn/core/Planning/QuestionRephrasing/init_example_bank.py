import os
from satyrn.core.Planning.QuestionRephrasing.ExampleBank import ExampleBank

# TODO: refactor this into env vars
# for spider dbs
# data_dir = "/Users/kevincushing/Documents/School/MS/Satyrn/sqrl-data-gen/generation/generated_data/spider/full_splits"

# for bird dbs
data_dir = "/Users/kevincushing/Documents/School/MS/Satyrn/sqrl-data-gen/generation/generated_data/bird/full_splits"

bank = ExampleBank()

# ONLY RUN THIS ONCE
# bank.load_examples(data_dir)
bank.load_examples(data_dir)


# TEST EXAMPLE BANK AFTER CREATION
# split = "train"
# db_id = "driving_school"
# question = "What are the Date Of Births and First Names for Staffs that have both Lessonss with lesson id equal to 5 and with lesson id equal to 6?"
# query = "SELECT Staff.date_of_birth AS c0, Staff.first_name AS c1  FROM Staff LEFT OUTER JOIN Lessons ON Staff.staff_id = Lessons.staff_id  WHERE Lessons.lesson_id = 5 INTERSECT SELECT Staff.date_of_birth AS c0, Staff.first_name AS c1  FROM Staff LEFT OUTER JOIN Lessons ON Staff.staff_id = Lessons.staff_id  WHERE Lessons.lesson_id = 6"

# exs = bank.query_examples(db_id, split, query, question)

# print(exs)