# Timesheet Management API - Product Requirements Document

## 1. Overview & Goals
- **Purpose:** Enable managers to create, read, update, and delete employee records and their monthly timesheets via a lightweight REST API.  
- **Success criteria:**  
  - Full CRUD on Employee and Timesheet objects.  
  - Enforce one timesheet per employee per calendar month.  
  - Store and retrieve monthly totals (working days, OT, Sunday work/OT).

---

## 2. User Stories

1. **Create & Manage Employees**  
   - **As a** manager  
   - **I want to** add a new employee with name, staff code, and UUID  
   - **So that** I can track timesheets against the correct person  

2. **View Employee List**  
   - **As a** manager  
   - **I want to** retrieve the list of all employees  
   - **So that** I can see who is in the system  

3. **Update Employee Details**  
   - **As a** manager  
   - **I want to** edit an employee’s name or staff code  
   - **So that** records stay accurate if details change  

4. **Delete Employee**  
   - **As a** manager  
   - **I want to** remove an employee  
   - **So that** their record and associated timesheets are no longer active  

5. **Create Monthly Timesheet**  
   - **As a** manager  
   - **I want to** submit a JSON payload with year, month, and totals for a given employee  
   - **So that** I capture that month’s work summary  

6. **Prevent Duplicates**  
   - **As a** manager  
   - **I want to** be prevented from creating a second timesheet for the same employee & month  
   - **So that** data remains consistent  

7. **View & Update Timesheet**  
   - **As a** manager  
   - **I want to** retrieve or update a specific month’s timesheet  
   - **So that** I can correct errors or verify details  

8. **Delete Timesheet**  
   - **As a** manager  
   - **I want to** delete an incorrect timesheet  
   - **So that** only valid records remain  

---

## 3. End-to-End Workflow

1. **Add Employee**  
   - Manager sends `POST /employees`  
   - System validates uniqueness of `staff_code` and assigns/returns `uuid`  
2. **List Employees**  
   - Manager sends `GET /employees`  
   - System returns array of all employees  

3. **Create Timesheet**  
   - Manager sends `POST /employees/{uuid}/timesheets` with:
     ```json
     {
       "year": 2025,
       "month": 6,
       "total_working_days": 22,
       "total_ot_hours": 5.5,
       "total_sundays_worked": 2,
       "total_ot_hours_on_sundays": 1.0
     }
     ```
   - System checks:
     - `(uuid, year, month)` not already present  
     - values non-negative, `total_sundays_worked ≤ total_working_days`  
   - On success, returns the created Timesheet record  

4. **View Timesheets**  
   - Manager can list all months:  
     `GET /employees/{uuid}/timesheets`  
   - Or fetch one month:  
     `GET /employees/{uuid}/timesheets/{year}/{month}`  

5. **Update Timesheet**  
   - Manager sends `PUT /employees/{uuid}/timesheets/{year}/{month}` with any changed totals  
   - System applies updates and returns the updated record  

6. **Delete Timesheet**  
   - Manager sends `DELETE /employees/{uuid}/timesheets/{year}/{month}`  
   - System removes the record  

7. **Update/Delete Employee**  
   - Manager sends `PUT /employees/{uuid}` or `DELETE /employees/{uuid}`  
   - System updates or cascades delete to timesheets (configurable)  

---

## 4. Data Model

### Employee
| Field       | Type   | Notes                  |
|-------------|--------|------------------------|
| `uuid`      | UUID   | PK                     |
| `staff_code`| string | Unique                 |
| `name`      | string |                        |

### Timesheet
| Field                        | Type   | Notes                                                       |
|------------------------------|--------|-------------------------------------------------------------|
| `id`                         | int    | Auto-increment PK                                           |
| `employee_uuid`              | UUID   | FK → Employee                                              |
| `year`                       | int    | 2000–2100                                                  |
| `month`                      | int    | 1–12                                                       |
| `total_working_days`         | int    | ≥ 0                                                        |
| `total_ot_hours`             | float  | ≥ 0                                                        |
| `total_sundays_worked`       | int    | ≥ 0, ≤ total_working_days                                  |
| `total_ot_hours_on_sundays`  | float  | ≥ 0                                                        |
| **Unique** `(employee_uuid, year, month)` |      | Prevent duplicates                                         |

---

## 5. API Endpoints

### Employee
| Method | Path                | Description               |
|--------|---------------------|---------------------------|
| GET    | `/employees`        | List all employees        |
| POST   | `/employees`        | Create employee           |
| GET    | `/employees/{uuid}` | Retrieve employee         |
| PUT    | `/employees/{uuid}` | Update employee           |
| DELETE | `/employees/{uuid}` | Delete employee & timesheets |

### Timesheet
| Method | Path                                                      | Description                  |
|--------|-----------------------------------------------------------|------------------------------|
| GET    | `/employees/{uuid}/timesheets`                            | List all timesheets         |
| GET    | `/employees/{uuid}/timesheets/{year}/{month}`             | Get one month’s timesheet   |
| POST   | `/employees/{uuid}/timesheets`                            | Create timesheet            |
| PUT    | `/employees/{uuid}/timesheets/{year}/{month}`             | Update timesheet            |
| DELETE | `/employees/{uuid}/timesheets/{year}/{month}`             | Delete timesheet            |

---

## 6. Validation Rules
- **Employees**  
  - `staff_code` unique, non-empty
- **Timesheets**  
  - `year` ∈ [2000,2100], `month` ∈ [1,12]  
  - All totals ≥ 0; `total_sundays_worked ≤ total_working_days`  
  - Reject duplicate `(uuid, year, month)`

---

## 7. Error Handling
- **400 Bad Request** – validation errors  
- **404 Not Found** – missing employee or timesheet  
- **409 Conflict** – duplicate staff_code or timesheet

---

## 8. Non-Functional Requirements
- **Performance:** GET <200 ms under light load  
- **Persistence:** SQLite (PoC); plan to swap to PostgreSQL  
- **Logging:** record errors and key request/response data  

---