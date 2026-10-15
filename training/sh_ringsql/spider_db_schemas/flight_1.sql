CREATE TABLE aircraft(
	aid number(9,0) primary key,
	name varchar2(30),
	distance number(6,0));

CREATE TABLE certificate(
	eid number(9,0),
	aid number(9,0),
	primary key(eid,aid),
	foreign key("eid") references `employee`("eid"),
	foreign key("aid") references `aircraft`("aid"));

CREATE TABLE employee(
	eid number(9,0) primary key,
	name varchar2(30),
	salary number(10,2));

CREATE TABLE flight(
	flno number(4,0) primary key,
	origin varchar2(20),
	destination varchar2(20),
	distance number(6,0),
	departure_date date,
	arrival_date date,
	price number(7,2),
    aid number(9,0),
    foreign key("aid") references `aircraft`("aid"));

