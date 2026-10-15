CREATE TABLE Allergy_Type (
       Allergy 		  VARCHAR(20) PRIMARY KEY,
       AllergyType 	  VARCHAR(20)
);

CREATE TABLE Has_Allergy (
       StuID 		 INTEGER,
       Allergy 		 VARCHAR(20),
       FOREIGN KEY(StuID) REFERENCES Student(StuID),
       FOREIGN KEY(Allergy) REFERENCES Allergy_Type(Allergy)
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

