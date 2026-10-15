CREATE TABLE AssignedTo (
  Scientist int not null,
  Project char(4) not null,
  Primary Key (Scientist, Project),
  Foreign Key (Scientist) references Scientists (SSN),
  Foreign Key (Project) references Projects (Code)
);

CREATE TABLE Projects (
  Code Char(4),
  Name Char(50) not null,
  Hours int,
  Primary Key (Code)
);

CREATE TABLE Scientists (
  SSN int,
  Name Char(30) not null,
  Primary Key (SSN)
);

