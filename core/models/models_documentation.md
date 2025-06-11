# CourseMap Data Models Documentation

This document provides an overview of the core data models used in the CourseMap ETL system.

## Table of Contents

1. [Overview](#overview)
2. [Program Model](#program-model)
3. [Course Model](#course-model)
4. [Relationships](#relationships)

## Overview

The CourseMap ETL system uses Pydantic models to represent academic program and course data. These models are generated from JSON schemas and provide type validation and data consistency across the application.

## Program Model

The program model (`UniversalProgramSchema`) represents academic programs such as majors, minors, certificates, etc.

### Key Components

#### ProgramType Enum

Defines the types of academic programs:

```python
class ProgramType(Enum):
    Major = 'Major'
    Minor = 'Minor'
    Cooperative = 'Cooperative'
    Concentration = 'Concentration'
    Certificate = 'Certificate'
    Diploma = 'Diploma'
    Doctoral = 'Doctoral'
    Masters = 'Master's'
```

#### CourseRef

References to courses within a program:

```python
class CourseRef(BaseModel):
    courseId: str
    code: str
    title: Optional[str] = None
    credits: Optional[float] = None
```

#### RequirementGroup

Groups of courses that fulfill specific program requirements:

```python
class RequirementGroup(BaseModel):
    groupId: str
    name: str
    description: Optional[str] = None
    creditsMin: Optional[float] = None
    creditsMax: Optional[float] = None
    courses: Optional[List[CourseRef]] = None
```

#### PanelItem

Informational panels about the program:

```python
class PanelItem(BaseModel):
    title: str
    paragraphs: Optional[List[str]] = None
    bulletList: Optional[List[str]] = None
```

#### UniversalProgramSchema

The main program model:

```python
class UniversalProgramSchema(BaseModel):
    programId: str
    code: str
    name: str
    description: Optional[str] = None
    url: Optional[AnyUrl] = None
    programTypes: List[ProgramType]
    degreeType: Optional[str] = None
    department: Optional[str] = None
    totalCredits: float
    creditBreakdown: Optional[Dict[str, float]] = None
    overview: Optional[List[str]] = None
    panels: Optional[List[PanelItem]] = None
    requirementGroups: Optional[List[RequirementGroup]] = None
    prerequisiteMap: Optional[Dict[str, List[str]]] = None
    corequisiteMap: Optional[Dict[str, List[str]]] = None
    notes: Optional[List[str]] = None
    extensions: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None
```

## Course Model

The course model (`UniversalCourseSchema`) represents individual academic courses.

### Key Components

#### Department

Represents an academic department:

```python
class Department(BaseModel):
    deptId: str = Field(..., description='System-generated unique ID.')
    code: Optional[str] = Field(None, description="School-local dept code (e.g. 'CS').")
    name: str = Field(..., description='Full dept/faculty name.')
    parentId: Optional[str] = Field(None, description='deptId of parent unit, if any.')
```

#### Season Enum

Defines academic seasons:

```python
class Season(Enum):
    Winter = 'Winter'
    Spring = 'Spring'
    Summer = 'Summer'
    Fall = 'Fall'
```

#### Term

Represents an academic term:

```python
class Term(BaseModel):
    termId: str = Field(..., description="Canonical ID, e.g. '2025FA'.")
    year: int = Field(..., description='Calendar year, e.g. 2025.')
    season: Season = Field(..., description='Season name.')
    startDate: Optional[date] = Field(None, description='Term start date.')
    endDate: Optional[date] = Field(None, description='Term end date.')
```

#### Instructor

Represents a course instructor:

```python
class Instructor(BaseModel):
    instructorId: str = Field(..., description='System-generated unique ID.')
    name: str = Field(..., description='Full name.')
    email: EmailStr = Field(..., description='Contact email.')
    role: Optional[str] = Field(None, description="Teaching role (e.g. 'Lecturer','TA').")
    departmentId: Optional[str] = Field(None, description='deptId of home department.')
```

#### Meeting Types and Schedule

```python
class Type(Enum):
    Lecture = 'Lecture'
    Lab = 'Lab'
    Tutorial = 'Tutorial'
    Exam = 'Exam'
    Other = 'Other'

class DayOfWeekEnum(Enum):
    Mon = 'Mon'
    Tue = 'Tue'
    Wed = 'Wed'
    Thu = 'Thu'
    Fri = 'Fri'
    Sat = 'Sat'
    Sun = 'Sun'

class Meeting(BaseModel):
    type: Type = Field(..., description='Block type.')
    dayOfWeek: List[DayOfWeekEnum] = Field(..., description='Days of week.')
    startTime: str = Field(..., pattern='^([01]\\d|2[0-3]):([0-5]\\d)$')
    endTime: str = Field(..., pattern='^([01]\\d|2[0-3]):([0-5]\\d)$')
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    location: Optional[str] = None
    raw: Optional[str] = Field(None, description='Original raw schedule text.')
```

#### Delivery Enum

Defines course delivery methods:

```python
class Delivery(Enum):
    InPerson = 'InPerson'
    Online = 'Online'
    Hybrid = 'Hybrid'
    Distance = 'Distance'
```

#### Section

Represents a course section:

```python
class Section(BaseModel):
    sectionId: str
    courseCode: str
    termId: str
    sectionCode: Optional[str] = None
    status: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=0)
    enrolled: Optional[int] = Field(None, ge=0)
    waitlist: Optional[int] = Field(None, ge=0)
    delivery: Optional[Delivery] = None
    instructors: Optional[List[Instructor]] = None
    meetings: Optional[List[Meeting]] = None
    raw: Optional[Dict[str, Any]] = Field(None, description='All raw source-section fields.')
```

#### UniversalCourseSchema

The main course model:

```python
class UniversalCourseSchema(BaseModel):
    courseId: str
    courseCode: str
    title: str
    description: Optional[str] = None
    department: Optional[Department] = None
    level: Optional[int] = Field(None, ge=0)
    credits: float = Field(..., ge=0.0)
    learningOutcomes: Optional[List[str]] = None
    countForPrograms: Optional[List[str]] = Field(None, description='Program codes this course counts toward.')
    excludeFromPrograms: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = Field(None, description='List of courseIds required first.')
    corequisites: Optional[List[str]] = None
    tags: Optional[List[str]] = Field(None, description='Keywords for interest-based search.')
    termsOffered: Optional[List[Term]] = None
    sections: Optional[List[Section]] = None
    extensions: Optional[Dict[str, Any]] = Field(None, description='Catch-all for school-specific extras.')
    raw: Optional[Dict[str, Any]] = Field(None, description='Top-level raw source fields.')
```

## Relationships

### Program to Course Relationships

- Programs reference courses through the `CourseRef` model in `requirementGroups`
- Programs can specify prerequisite and corequisite relationships between courses via `prerequisiteMap` and `corequisiteMap`

### Course to Program Relationships

- Courses can specify which programs they count toward via `countForPrograms`
- Courses can specify which programs they are excluded from via `excludeFromPrograms`

### Course to Course Relationships

- Courses can specify prerequisite courses via `prerequisites`
- Courses can specify corequisite courses via `corequisites`

## Usage Examples

### Creating a Program

```python
from core.models.program import UniversalProgramSchema, ProgramType, RequirementGroup, CourseRef

program = UniversalProgramSchema(
    programId="CS-BSC-2025",
    code="CS-BSC",
    name="Bachelor of Science in Computer Science",
    programTypes=[ProgramType.Major],
    totalCredits=120.0,
    requirementGroups=[
        RequirementGroup(
            groupId="core",
            name="Core Courses",
            creditsMin=60.0,
            courses=[
                CourseRef(courseId="CS101", code="CS101", title="Introduction to Programming", credits=3.0),
                CourseRef(courseId="CS102", code="CS102", title="Data Structures", credits=3.0),
            ]
        )
    ]
)
```

### Creating a Course

```python
from core.models.course import UniversalCourseSchema, Department

course = UniversalCourseSchema(
    courseId="CS101",
    courseCode="CS101",
    title="Introduction to Programming",
    credits=3.0,
    department=Department(
        deptId="CS",
        code="CS",
        name="Computer Science"
    ),
    prerequisites=[]
)
```