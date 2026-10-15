CREATE TABLE Plays_Games (
       StuID                INTEGER,
       GameID            INTEGER,
       Hours_Played      INTEGER,
       FOREIGN KEY(GameID) REFERENCES Video_Games(GameID),
       FOREIGN KEY(StuID) REFERENCES Student(StuID)
);

CREATE TABLE SportsInfo (
  StuID INTEGER,
  SportName VARCHAR(32),
  HoursPerWeek INTEGER,
  GamesPlayed INTEGER,
  OnScholarship VARCHAR(1),
  FOREIGN KEY(StuID) REFERENCES Student(StuID)
);

CREATE TABLE Student (
        StuID        INTEGER PRIMARY KEY,
        LName        VARCHAR(12),
        Fname        VARCHAR(12),
        Age      INTEGER,
        Sex      VARCHAR(1),
        Major        INTEGER,
        Advisor      INTEGER,
        city_code    VARCHAR(3)
 );

CREATE TABLE Video_Games (
       GameID           INTEGER PRIMARY KEY,
       GName            VARCHAR(40),
       GType            VARCHAR(40)
);

