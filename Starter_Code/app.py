#Imports
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc
from flask import Flask, jsonify

#Database Setup
path = "Starter_Code\Resources\hawaii.sqlite"
engine = create_engine(f"sqlite:///{path}")


#Pull an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

#View all of the automap classes 
Base.classes.keys()

#Table references
measurement = Base.classes.measurement
station = Base.classes.station


#Flask Setup

app = Flask(__name__)

#Flask Routes

@app.route("/") 
@app.route('/home')
def homepage():
    #Listing avaiable API roots
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>" 
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start/end<br/>" 
    )


#Precipitation route

@app.route('/api/v1.0/precipitation')
def precipitation():
    #Open session
    session = Session(engine)

    results = session.query(measurement.date, measurement.prcp).all()
    
    #Close session
    session.close()

    precipitation_inclusive = []

    for date, prcp in results:
        dictionary = {}
        dictionary[date] = prcp

        precipitation_inclusive.append(dictionary)
    
    return jsonify(precipitation_inclusive)


#stations route

@app.route('/api/v1.0/stations')
def stations():
    #Open session
    session = Session(engine)

    results = session.query(station.station).all()
    
    #Close session
    session.close()

    return jsonify(list(np.ravel(results)))


#tobs route

@app.route('/api/v1.0/tobs')
def tobs():
    #Open session
    session = Session(engine)

    most_active_stations = (session
                            .query(measurement.station, func.count(measurement.station).label('count'))
                            .group_by(measurement.station)
                            .order_by(desc('count'))
                            .all())
    station_last_date = (session.query(func.max(measurement.date))
                         .filter(measurement.station == most_active_stations[0][0])
                         .scalar())
    
    #Convert station_last_date to a datetime object
    station_last_date = dt.datetime.strptime(station_last_date, '%Y-%m-%d').date()

    #Calculate one year prior
    year_prior = station_last_date - dt.timedelta(days=365)
    
    #Perform left join for the measurment and station tables
    stations= (session.query(measurement, station.name)
               .outerjoin(station, measurement.station == station.station)
               .filter(measurement.station == most_active_stations[0][0])
               .filter(measurement.date >= str(year_prior))
               .all())

    #Close session
    session.close()

    #Loop over the query to fetch the results for the json
    results = []
    for row in stations:
        measurement_data = {
            'date': row[0].date,
            'tobs': row[0].tobs,
            'station': row[0].station,
            'station_name': row[1]  
        }
        results.append(measurement_data)

    return jsonify(results)





#start_date Route

@app.route('/api/v1.0/<start_date>')
def start_date(start_date):
    try:
        #Convert the input date string to a datetime object
        start = dt.datetime.strptime(start_date, '%Y-%m-%d').date()

        #Open session
        session = Session(engine)

        #Query the results from start date based on a user input
        results = (session.query(
            func.min(measurement.tobs).label('min'),
            func.avg(measurement.tobs).label('avg'),
            func.max(measurement.tobs).label('max')
        ).filter(measurement.date >= start)
        .group_by(measurement.date)
        .all())

        #Close session
        session.close()

        result_dict = []

        for row in results:
            dictionary = {
                'min': row.min,
                'avg': row.avg,
                'max': row.max
            }


            result_dict.append(dictionary)

        return jsonify(result_dict)

    except ValueError:
        # If the date format is incorrect, return an error message
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400
    

# <start_date>/<end> Route

@app.route('/api/v1.0/<start_date>/<end>')
def start_end(start_date, end):
    try:
        #Convert the input date string to a datetime object
        start = dt.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = dt.datetime.strptime(end, '%Y-%m-%d').date()

        #Open session
        session = Session(engine)

        #Query the results based on the start and end periods provided by the user 
        results = (session.query(
            func.min(measurement.tobs).label('min'),
            func.avg(measurement.tobs).label('avg'),
            func.max(measurement.tobs).label('max')
        ).filter(measurement.date >= start, measurement.date <= end_date)
        .group_by(measurement.date)
        .all())

        #Close session
        session.close()

        #Creating a dictionary to store query results prior to json
        result_dict = []
        for row in results:
            dictionary = {
                'min': row.min,
                'avg': row.avg,
                'max': row.max
            }
            result_dict.append(dictionary)

        return jsonify(result_dict)

    except ValueError:
        #If the date format is incorrect, return an error message
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400


if __name__ == '__main__':
    app.run(debug=True)