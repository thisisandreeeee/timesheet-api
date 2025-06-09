# Timesheet API Test Documentation

## Overview

This document outlines the test strategy and test cases for the Timesheet API, focusing on the employee and timesheet endpoints. The tests are organized to validate the end-to-end workflow and ensure all API functionality works as expected.

## Test Environment

- **Base URL**: `http://localhost:8000`
- **Tools**: Postman for API testing
- **Authentication**: None (API does not require authentication)

## End-to-End Workflow

The typical workflow for the Timesheet API follows these steps:

1. Create an employee
2. Create a timesheet for that employee
3. View the employee's timesheet(s)
4. Update the timesheet
5. Delete the timesheet
6. Delete the employee

## Test Categories

### 1. Health Check Tests

These tests verify that the API is up and running:

- **Health Check**: Verify the `/health` endpoint returns a 200 status code and a status of "ok"
- **Root Endpoint**: Verify the root endpoint (`/`) returns a 200 status code and a welcome message

### 2. Employee Management Tests

These tests verify the CRUD operations for employees:

#### 2.1. Create Employee Tests

- **Create Employee (Success)**: Verify that an employee can be created successfully with valid data
- **Create Employee (Duplicate)**: Verify that attempting to create an employee with a duplicate staff code returns a 409 Conflict error
- **Create Employee (Invalid)**: Verify that attempting to create an employee with invalid data (e.g., empty staff code) returns a 422 Unprocessable Entity error

#### 2.2. Read Employee Tests

- **Get All Employees**: Verify that all employees can be retrieved
- **Get Employee by UUID**: Verify that a specific employee can be retrieved by UUID
- **Get Employee (Not Found)**: Verify that attempting to retrieve a non-existent employee returns a 404 Not Found error

#### 2.3. Update Employee Tests

- **Update Employee**: Verify that an employee can be updated successfully

#### 2.4. Delete Employee Tests

- **Delete Employee**: Verify that an employee can be deleted successfully

### 3. Timesheet Management Tests

These tests verify the CRUD operations for timesheets:

#### 3.1. Create Timesheet Tests

- **Create Timesheet (Success)**: Verify that a timesheet can be created successfully with valid data
- **Create Timesheet (Duplicate)**: Verify that attempting to create a duplicate timesheet for the same employee, year, and month returns a 409 Conflict error
- **Create Timesheet (Invalid)**: Verify that attempting to create a timesheet with invalid data (e.g., more Sundays than working days) returns a 422 Unprocessable Entity error

#### 3.2. Read Timesheet Tests

- **Get All Timesheets**: Verify that all timesheets for an employee can be retrieved
- **Get Specific Timesheet**: Verify that a specific timesheet can be retrieved by employee UUID, year, and month
- **Get Timesheet (Not Found)**: Verify that attempting to retrieve a non-existent timesheet returns a 404 Not Found error

#### 3.3. Update Timesheet Tests

- **Update Timesheet**: Verify that a timesheet can be updated successfully

#### 3.4. Delete Timesheet Tests

- **Delete Timesheet**: Verify that a timesheet can be deleted successfully

## Data Validation Tests

The API includes several validation rules that are tested:

1. Employee staff code cannot be empty
2. Employee name cannot be empty
3. Timesheet year must be between 2000 and 2100
4. Timesheet month must be between 1 and 12
5. Timesheet total working days must be greater than or equal to 0
6. Timesheet total overtime hours must be greater than or equal to 0
7. Timesheet total Sundays worked must be greater than or equal to 0
8. Timesheet total overtime hours on Sundays must be greater than or equal to 0
9. Timesheet total Sundays worked cannot exceed total working days

## Error Handling Tests

The API should return appropriate error responses in different scenarios:

1. 404 Not Found: When attempting to access a resource that doesn't exist
2. 409 Conflict: When attempting to create a resource that already exists
3. 422 Unprocessable Entity: When providing invalid data

## Running the Tests

1. Import the Postman collection (`Timesheet_API_Tests.postman_collection.json`) into Postman
2. Import the Postman environment (`Timesheet_API_Environment.postman_environment.json`) into Postman
3. Select the "Timesheet API Environment" environment
4. Run the collection in the following order:
   - Health Check
   - Employee Management
   - Timesheet Management
   - Cleanup

## Test Data Management

The tests use dynamic data generation and environment variables to maintain state between requests:

- Random staff codes and names are generated for employees
- The employee UUID is stored in the environment for use in subsequent requests
- Timesheet data is stored in the environment for use in subsequent requests

## Expected Results

All tests should pass with the following status codes:

- 200 OK: For successful GET and PUT requests
- 201 Created: For successful POST requests
- 204 No Content: For successful DELETE requests
- 404 Not Found: For requests to non-existent resources
- 409 Conflict: For requests that conflict with existing resources
- 422 Unprocessable Entity: For requests with invalid data 