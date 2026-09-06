The root directory will contain a `data` dir organised like so:

```mermaid
treeView-beta
    data/
        seed/                      # files provided by the developer to setup the DB and other pre-reqs
            something.sql   # SQL files to run on the DB like DDLs, initial seed data etc
            something.csv   # CSV files to load into the DB
        tests/
            tc001/                    # file(s) for test case 001
                something.csv   
            ...
    src/
        ...
```

A `src` layout will be used for code.

`uv` is used for package management

`just` is available to automate repetitive tasks if needed
