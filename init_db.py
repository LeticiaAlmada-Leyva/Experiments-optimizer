from database import engine, Base
import models

# Genera la tabla en el archivo carbon_dots.db
Base.metadata.create_all(bind=engine)
print("Database and table 'Experiments' created sucessfully!!")