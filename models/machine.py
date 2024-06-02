from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Creating the Inserttable for inserting data into the database


class Inserttable(db.Model):
    '''Data for ON/OFF should be dumped in this table.'''

    __tablename__ = 'inserttable'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    machineid = db.Column(db.Integer, primary_key=False)
    stateid = db.Column(db.Integer, primary_key=False)
    speed = db.Column(db.Integer, nullable=False)
    statechange = db.Column(db.Integer, nullable=False)
    unixtime = db.Column(db.Integer, nullable=False)
    extras = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)

    # method used to represent a class's objects as a string
    def __repr__(self):
        return '<machineid %r>' % self.machineid