# Tools used in the project
The following lists the tools and frameworks, that are used in the project. 
- [Docker](https://docs.docker.com/get-started/overview/)    
   Docker is an open platform for developing, shipping, and running applications. Docker enables you to separate your applications from your infrastructure so you can deliver software quickly. With Docker, you can manage your infrastructure in the same ways you manage your applications. By taking advantage of Docker's methodologies for shipping, testing, and deploying code, you can significantly reduce the delay between writing code and running it in production.
- [Kubernetes](https://kubernetes.io/docs/concepts/overview/)
   Kubernetes is a portable, extensible, open source platform for managing containerized workloads and services, that facilitates both declarative configuration and automation. It has a large, rapidly growing ecosystem. Kubernetes services, support, and tools are widely available.
- [FastAPI](https://fastapi.tiangolo.com/tutorial/)
   FastAPI is a modern, fast (high-performance), web framework for building APIs with Python based on standard Python type hints.
- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)
    SQLAlchemy is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
    It provides a full suite of well known enterprise-level persistence patterns, designed for efficient and high-performing database access, adapted into a simple and Pythonic domain language.
- [FastAPI with SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)
    Integrating FastAPI with SQLAlchemy enables the creation of high-performance, scalable APIs with robust database interactions.
- [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
  Alembic is a database migrations tool written by the author of SQLAlchemy. A migrations tool offers the following functionality:
  Can emit ALTER statements to a database in order to change the structure of tables and other constructs
  Provides a system whereby "migration scripts" may be constructed; each script indicates a particular series of steps that can "upgrade" a target database to a new version, and optionally a series of steps that can "downgrade" similarly, doing the same steps in reverse.
  Allows the scripts to execute in some sequential manner.
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
    Swagger UI allows anyone — be it your development team or your end consumers — to visualize and interact with the API’s resources without having any of the implementation logic in place. It’s automatically generated from your OpenAPI (formerly known as Swagger) Specification, with the visual documentation making it easy for back end implementation and client side consumption.
- [Ruff](https://github.com/astral-sh/ruff)
    An extremely fast Python linter and code formatter, written in Rust.



# GitLab CI/CD

The following is a collection of short hints on how to do the most essential things in a GitLab CI/CD pipeline:

- How to delay a job until another job is done: needs:[other_job]

- How to change the image used in a task: image: your_image
    
- How do you start a task manually: when: manual

- The Script part of the config file - what is it good for? : diese section bestimmt was genau der job macht

- If I want a task to run for every branch I put it into the stage test

- If I want a task to run for every merge request I put it into the stage test

- If I want a task to run for every commit to the main branch I put it into the stage deploy

# Ruff

- What is the purpose of ruff:
Ruff is an extremely fast Python linter and code formatter. Its purpose is to find errors in your code, enforce a consistent style, and automatically format your code, all from a single tool. It's written in Rust to be 10-100x faster than tools like Flake8, Black, and isort, which it is designed to replace.


- What types of problems does it detect: 

As a linter, Ruff detects hundreds of different problems, which can be grouped into a few main categories:

Logical Errors: Such as unused variables, undefined names, or code that can never be reached.

Style Violations: Like lines that are too long, incorrect naming conventions, or improper spacing.

Bad Practices: Including inefficient code patterns (e.g., unnecessary loops) and common "gotchas" that can lead to bugs.

Import-Related Issues: It detects and can automatically fix unsorted or incorrectly grouped imports.

- Why should you use a tool like ruff in a serious project? :

There are three key reasons:

Enforces Code Consistency: It guarantees that all code, no matter which developer wrote it, follows the same style. This ends debates about formatting and makes the code base significantly easier to read and maintain.

Boosts Productivity (Speed): It runs almost instantly, giving developers immediate feedback instead of making them wait. This also makes CI/CD pipelines (automated checks) dramatically faster.

Simplifies Tooling: It consolidates 5-10 different tools (like Flake8, Black, isort, pydocstyle, etc.) into one. This simplifies your project's setup, reduces dependencies, and makes configuration much easier.

## Run ruff on your local Computer

  It is very annoying (and takes a lot of time) to wait for the pipeline to check the syntax 
  of your code. To speed it up, you may run it locally like this:

### Configure PyCharm (only once)
- find out the name of your docker container containing ruff. Open the tab *services* in PyCharm and look at the container in the service called *web*. The the name should contain the string *1337_pizza_web_dev*.  
- select _Settings->Tools->External Tools_ 
- select the +-sign (new Tool)
- enter Name: *ruff-docker*
- enter Program: *docker*
- enter Arguments (replace the first parameter with the name of your container): 
    *exec -i NAMEOFYOURCONTAINER ruff check --exclude /opt/project/app/api/database/migrations/ /opt/project/app/api/ /opt/project/tests/*
- enter Working Directory: *\$ProjectFileDir\$*

If you like it convenient: Add a button for ruff to your toolbar!
- right click into the taskbar (e.g. on one of the git icons) and select *Customize ToolBar*
- select the +-sign and Add Action
- select External Tools->ruff-docker

### Run ruff on your project
  - Remember! You will always need to run the docker container called *1337_pizza_web_dev* of your project, to do this! 
    So start the docker container(s) locally by running your project
  - Now you may run ruff 
      - by clicking on the new icon in your toolbar or 
      - by selecting from the menu: Tools->External Tools->ruff-docker 

# GrayLog

- What is the purpose of GrayLog?

- What logging levels are available?

- What is the default logging level?

- Give 3-4 examples for logging commands in Python:
  ```python

  ```

# SonarQube

- What is the purpose of SonarQube?
SonarQube is a static code analyzer which checks if your code is compliant with a pre defined set of rules

- What is the purpose of the quality rules of SonarQube?
all of the code is checked for compliance with this ruleset and is meant to ensure high quality code
which is maintainable and secure

- What is the purpose of the quality gates of SonarQube?
quality gates check if your code is ready for release by ensuring it is compliant with the pre defined standards


## Run SonarLint on your local Computer

It is very annoying (and takes a lot of time) to wait for the pipeline to run SonarQube. 
To speed it up, you may first run the linting part of SonarQube (SonarLint) locally like this:

### Configure PyCharm for SonarLint (only once)

- Open *Settings->Plugins*
- Choose *MarketPlace*
- Search for *SonarLint* and install the PlugIn

### Run SonarLint

- In the project view (usually to the left) you can run the SonarLint analysis by a right click on a file or a folder. 
  You will find the entry at the very bottom of the menu.
- To run it on all source code of your project select the folder called *app*

# VPN

The servers providing Graylog, SonarQube and your APIs are hidden behind the firewall of Hochschule Darmstadt.
From outside the university it can only be accessed when using a VPN.
https://its.h-da.io/stvpn-docs/de/ 