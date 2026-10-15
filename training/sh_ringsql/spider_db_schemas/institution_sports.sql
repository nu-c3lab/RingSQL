CREATE TABLE "Championship" (
"Institution_ID" int,
"Nickname" text,
"Joined" real,
"Number_of_Championships" real,
PRIMARY KEY ("Institution_ID"),
FOREIGN KEY ("Institution_ID") REFERENCES `institution`("Institution_ID")
);

CREATE TABLE "institution" (
"Institution_ID" int,
"Name" text,
"Team" text,
"City" text,
"Province" text,
"Founded" real,
"Affiliation" text,
"Enrollment" real,
"Endowment" text,
"Stadium" text,
"Capacity" real,
PRIMARY KEY ("Institution_ID")
);

