CREATE DATABASE IF NOT EXISTS studentdb;
USE studentdb;

CREATE TABLE IF NOT EXISTS students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(10),
    fullname VARCHAR(100),
    dob DATE,
    major VARCHAR(50)
);

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('ABY01', 'Sunaookami Shiroko', '2008-05-16', 'Sports Science');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('ABY02', 'Takanashi Hoshino', '2007-01-08', 'Security Operations');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('GEH01', 'Rikuhachima Aru', '2008-03-12', 'Business Administration');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('GEH02', 'Sorasaki Hina', '2007-02-19', 'Public Administration');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('MIL01', 'Hayase Yuuka', '2008-11-09', 'Applied Mathematics');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('MIL02', 'Nekozuka Hibiki', '2008-07-25', 'Audio Engineering');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('TRI01', 'Misono Mika', '2008-08-01', 'Political Science');

INSERT INTO students (student_id, fullname, dob, major) 
VALUES ('TRI02', 'Shirasu Azusa', '2008-12-24', 'Philosophy');