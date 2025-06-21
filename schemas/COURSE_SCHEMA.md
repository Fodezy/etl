# Universal Course Schema - Technical Documentation

**Version:** 09
**Schema Definition:** \`universal-course.draft-09.json\`

## 1. Introduction

This document provides detailed technical documentation for the Universal Course Schema (UCS), a canonical, school-agnostic schema for representing university and college course catalog data. It is intended for developers, data architects, and analysts who will be creating, validating, or consuming data that conforms to this schema.

The schema is designed to be comprehensive and flexible, capable of handling a wide variety of course structures, scheduling patterns, and requisite rules from different academic institutions. It provides a standardized format that allows for easier data exchange, aggregation, and analysis across different systems.

## 2. Core Concepts & Data Model

The schema is centered around the \`Course\` object. A \`Course\` is the primary entity, representing an abstract subject of study (e.g., "Introduction to Psychology"). A \`Course\` can have one or more \`Section\` objects associated with it for a given academic term, where a \`Section\` represents a specific offering that a student can enroll in.

The main data objects and their relationships are as follows:

- **\`Course\`**: The top-level object. It contains general information like the course code, title, description, credit value, and requisite rules.
  - **One-to-One with \`Department\`**: Each \`Course\` is offered by one primary \`Department\`.
  - **One-to-Many with \`Section\`**: A \`Course\` can have many \`Section\`s offered over time.
  - **One-to-Many with \`OfferingPattern\`**: A \`Course\` may have general patterns describing when it is typically offered (e.g., "Every Fall").
- **\`Section\`**: A specific instance of a course offered in a particular \`Term\`. It has details like capacity, enrollment numbers, and specific meeting times.
  - **Many-to-Many with \`Instructor\`**: A \`Section\` can be taught by one or more \`Instructor\`s.
  - **One-to-Many with \`Meeting\`**: A \`Section\` is composed of one or more scheduled \`Meeting\`s (e.g., a lecture every Monday/Wednesday and a lab every Friday).
- **\`Department\`**: An academic unit, like "Computer Science" or "Faculty of Arts." Can be hierarchical.
- **\`Term\`**: A specific academic period, like "Fall 2025".
- **\`Instructor\`**: A person associated with teaching a section.
- **\`Meeting\`**: A scheduled block of time for a section, including day, time, and location.
- **\`RequisiteExpression\`**: A powerful, recursive object used to define complex prerequisite and corequisite rules in a structured, machine-readable way.

---

## 3. Schema Reference

This section details the properties of the main object and all object definitions (`$defs`).

### 3.1 \`Course\` Object

The root object representing a single course.

| Property               | Type                     | Required | Description                                                                                                       |
| ---------------------- | ------------------------ | :------: | ----------------------------------------------------------------------------------------------------------------- |
| \`courseId\`           | string                   | **Yes**  | A canonical, globally unique ID for the course.                                                                   |
| \`courseCode\`         | string                   | **Yes**  | The school-specific code (e.g., 'CS101', 'ACCT\*1220').                                                           |
| \`title\`              | string                   | **Yes**  | The official title of the course.                                                                                 |
| \`credits\`            | number                   | **Yes**  | The academic credit value of the course (e.g., 0.5, 3.0).                                                         |
| \`description\`        | string                   |    No    | A comprehensive descriptive text for the course.                                                                  |
| \`department\`         | object                   |    No    | The primary academic department offering the course. See [\`Department\`](#32-department).                        |
| \`level\`              | integer                  |    No    | The academic level (e.g., 1000 for 1st year, 2000 for 2nd).                                                       |
| \`prerequisites\`      | object \| string \| null |    No    | Structured requisite rules, a raw text string, or null. See [\`RequisiteExpression\`](#38-requisiteexpression).   |
| \`corequisites\`       | object \| string \| null |    No    | Structured corequisite rules, a raw text string, or null. See [\`RequisiteExpression\`](#38-requisiteexpression). |
| \`antirequisites\`     | array of strings         |    No    | An array of course codes that grant equivalent credit and cannot be taken.                                        |
| \`crossListings\`      | array of strings         |    No    | An array of other course codes this course is also listed as.                                                     |
| \`tags\`               | array of strings         |    No    | Keywords for search or categorization (e.g., 'Quantitative', 'Science Elective').                                 |
| \`termsOffered\`       | array of objects         |    No    | Describes the general pattern of when the course is offered. See [\`OfferingPattern\`](#37-offeringpattern).      |
| \`courseStatus\`       | enum                     |    No    | The current status of the course (\`Active\`, \`Inactive\`, \`New\`, etc.).                                       |
| \`effectiveStartDate\` | string (date)            |    No    | The date from which this version of the course information is effective.                                          |
| \`effectiveEndDate\`   | string (date)            |    No    | The date until which this version of the course information is effective.                                         |
| \`sections\`           | array of objects         |    No    | A list of specific offerings for this course. See [\`Section\`](#36-section).                                     |
| \`extensions\`         | object                   |    No    | A catch-all object for non-standard, school-specific data.                                                        |
| \`raw\`                | object                   |    No    | The original, unmodified source data for this course, for archival.                                               |

---

### 3.2 \`Department\`

| Property     | Type   | Required | Description                                                          |
| ------------ | ------ | :------: | -------------------------------------------------------------------- |
| \`deptId\`   | string | **Yes**  | A system-generated, unique ID for the department.                    |
| \`name\`     | string | **Yes**  | The full name of the department (e.g., "Department of Philosophy").  |
| \`code\`     | string |    No    | The school-local code (e.g., 'PHIL').                                |
| \`parentId\` | string |    No    | The \`deptId\` of the parent faculty or unit, if this is a sub-unit. |

---

### 3.3 \`Term\`

| Property      | Type          | Required | Description                                                         |
| ------------- | ------------- | :------: | ------------------------------------------------------------------- |
| \`termId\`    | string        | **Yes**  | Canonical ID for the term (e.g., '2025FA' for Fall 2025).           |
| \`year\`      | integer       | **Yes**  | The calendar year of the term (e.g., 2025).                         |
| \`season\`    | enum          | **Yes**  | The academic season (\`Winter\`, \`Spring\`, \`Summer\`, \`Fall\`). |
| \`startDate\` | string (date) |    No    | The official start date of the term.                                |
| \`endDate\`   | string (date) |    No    | The official end date of the term.                                  |

---

### 3.4 \`Instructor\`

| Property         | Type           | Required | Description                                                         |
| ---------------- | -------------- | :------: | ------------------------------------------------------------------- |
| \`instructorId\` | string         | **Yes**  | A system-generated, unique ID for the instructor.                   |
| \`name\`         | string         | **Yes**  | The full name of the instructor.                                    |
| \`email\`        | string (email) | **Yes**  | The contact email address.                                          |
| \`role\`         | string         |    No    | The role in the section (e.g., 'Lecturer', 'Lab Instructor', 'TA'). |
| \`departmentId\` | string         |    No    | The \`deptId\` of the instructor's home department.                 |

---

### 3.5 \`Meeting\`

| Property      | Type               | Required | Description                                                     |
| ------------- | ------------------ | :------: | --------------------------------------------------------------- |
| \`type\`      | enum               | **Yes**  | The type of meeting (\`Lecture\`, \`Lab\`, \`Seminar\`, etc.).  |
| \`dayOfWeek\` | array of enums     |    No    | Days the meeting occurs (\`Mon\`, \`Tue\`, etc.).               |
| \`startTime\` | string (\`HH:MM\`) |    No    | The start time in 24-hour format.                               |
| \`endTime\`   | string (\`HH:MM\`) |    No    | The end time in 24-hour format.                                 |
| \`startDate\` | string (date)      |    No    | Start date if different from term start.                        |
| \`endDate\`   | string (date)      |    No    | End date if different from term end.                            |
| \`location\`  | string             |    No    | The building and room number (e.g., "Mackinnon 113").           |
| \`raw\`       | string             |    No    | The original, unparsed schedule text (e.g., "MWF 10:30-11:20"). |

---

### 3.6 \`Section\`

| Property        | Type             | Required | Description                                                                    |
| --------------- | ---------------- | :------: | ------------------------------------------------------------------------------ |
| \`sectionId\`   | string           | **Yes**  | A unique ID for this specific section offering.                                |
| \`courseCode\`  | string           | **Yes**  | The course code this section belongs to.                                       |
| \`termId\`      | string           | **Yes**  | The term ID in which this section is offered.                                  |
| \`sectionCode\` | string           |    No    | The specific section number (e.g., '0101', 'A').                               |
| \`status\`      | string           |    No    | The enrollment status (e.g., 'Open', 'Closed', 'Waitlist').                    |
| \`capacity\`    | integer          |    No    | The maximum number of students allowed.                                        |
| \`enrolled\`    | integer          |    No    | The current number of students enrolled.                                       |
| \`waitlist\`    | integer          |    No    | The number of students on the waitlist.                                        |
| \`delivery\`    | enum             |    No    | The delivery mode (\`InPerson\`, \`Online\`, \`Hybrid\`).                      |
| \`instructors\` | array of objects |    No    | A list of instructors for this section. See [\`Instructor\`](#34-instructor).  |
| \`meetings\`    | array of objects |    No    | A list of scheduled meetings for this section. See [\`Meeting\`](#35-meeting). |
| \`raw\`         | object           |    No    | The original, unmodified source data for this section.                         |

---

### 3.7 \`OfferingPattern\`

| Property  | Type           | Required | Description                                                                 |
| --------- | -------------- | :------: | --------------------------------------------------------------------------- |
| \`terms\` | array of enums |    No    | An array of seasons the course is typically offered (\`Fall\`, \`Winter\`). |
| \`years\` | array of enums |    No    | The frequency pattern (\`Annually\`, \`Even\` years, \`Odd\` years, etc.).  |
| \`note\`  | string         |    No    | A free-text note about the offering pattern (e.g., "Offered in F, W, S").   |

---

### 3.8 \`RequisiteExpression\`

The \`RequisiteExpression\` object provides a structured, recursive way to define complex requirements. It can be thought of as a tree where the nodes represent logical operators or specific conditions.

| \`type\` value               | Required Properties                           | Description                                                                                                                  |
| ---------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| \`AND\`                      | \`expressions\`                               | All nested expressions must be met.                                                                                          |
| \`OR\`                       | \`expressions\` or \`courses\`                | At least one of the nested expressions or listed courses must be met.                                                        |
| \`N_OF\`                     | \`count\`, and \`expressions\` or \`courses\` | A minimum number (\`count\`) of the nested expressions or courses must be met.                                               |
| \`COURSE\`                   | \`courses\` (with 1 item)                     | A specific course is required.                                                                                               |
| \`CREDITS\`                  | \`credits\`                                   | A minimum number of total academic credits is required.                                                                      |
| \`SUBJECT_CREDITS\`          | \`credits\`, \`subject\`                      | A minimum number of credits in a specific subject is required.                                                               |
| \`SUBJECT_CREDITS_AT_LEVEL\` | \`credits\`, \`subject\`, \`level\`           | A minimum number of credits in a subject at or above a certain level.                                                        |
| \`MIN_GRADE\`                | \`course\`, \`percentage\`                    | A minimum grade in a specific course is required.                                                                            |
| \`MIN_AVERAGE\`              | \`percentage\`                                | A minimum overall academic average is required.                                                                              |
| \`PROGRAM_REGISTRATION\`     | \`program\`                                   | Student must be registered in a specific academic program.                                                                   |
| \`EXCLUDE_COURSE\`           | \`courses\`                                   | A student who has taken any of the listed courses is excluded.                                                               |
| \`RAW_UNPARSED\`             | \`value\`                                     | The requirement could not be parsed and is stored as a raw string.                                                           |
| \`EQUIVALENT\`               | _none_                                        | Represents an equivalency credit that cannot be used as a prerequisite. This is a terminal node and has no other properties. |
| _Other Types_                | \`description\` or other specific fields      | Other miscellaneous requirements (e.g., \`HIGHSCHOOL_REQUIREMENT\`).                                                         |

#### \`RequisiteExpression\` Examples

**Example 1: Simple Prerequisite** _Requirement: Must have completed \`CS101\`._

```json
{
  "type": "COURSE",
  "courses": ["CS101"]
}
```

**Example 2: Two Prerequisites (AND)** _Requirement: Must have completed \`MATH101\` AND \`STAT101\`._

```json
{
  "type": "AND",
  "expressions": [
    { "type": "COURSE", "courses": ["MATH101"] },
    { "type": "COURSE", "courses": ["STAT101"] }
  ]
}
```

**Example 3: Choice of Prerequisite (OR)** _Requirement: Must have completed \`PHYS101\` OR \`PHYS102\`._

```json
{
  "type": "OR",
  "courses": ["PHYS101", "PHYS102"]
}
```

**Example 4: "2 of the following" (N_OF)** _Requirement: 2 credits from (\`HIST100\`, \`HIST110\`, \`HIST120\`)._

```json
{
  "type": "N_OF",
  "count": 2,
  "courses": ["HIST100", "HIST110", "HIST120"]
}
```

**Example 5: Nested Logic** _Requirement: (\`CS150\` and \`CS155\`) OR (\`CS160\` and 1 of (\`MATH110\`, \`MATH120\`))._

```json
{
  "type": "OR",
  "expressions": [
    {
      "type": "AND",
      "expressions": [
        { "type": "COURSE", "courses": ["CS150"] },
        { "type": "COURSE", "courses": ["CS155"] }
      ]
    },
    {
      "type": "AND",
      "expressions": [
        { "type": "COURSE", "courses": ["CS160"] },
        { "type": "OR", "courses": ["MATH110", "MATH120"] }
      ]
    }
  ]
}
```

**Example 6: Minimum Grade** _Requirement: A minimum grade of 75% in \`CHEM101\`._

```json
{
  "type": "MIN_GRADE",
  "course": "CHEM101",
  "percentage": 75
}
```
