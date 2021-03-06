import os

import click
from flask import current_app
from flask.cli import with_appcontext
import requests

from pushpull.model import Student, Teacher, db


AERIES_CERT = os.getenv('AERIES_CERT')
AERIES_API_BASE = os.getenv('AERIES_API_BASE')

SCHOOL_ID = 1
HOME_COURSE_ID = '2604'


def get_endpoint(*components):
    headers = {'AERIES-CERT': AERIES_CERT}
    endpoint = '/'.join(map(str, components))
    url = f'{AERIES_API_BASE}/api/v5/{endpoint}'
    return requests.get(url, headers=headers).json()


def school_endpoint(school_code, endpoint):
    return endpoint(f'schools/{school_code}/{endpoint}')


@click.command('sync')
@with_appcontext
def sync_command():
    click.echo('Performing Aeries data sync.')

    # Get from the current school
    do_get = lambda e: get_endpoint('schools', SCHOOL_ID, e)

    click.echo('Pulling teacher info from Aeries...')
    staff = {s['ID']: s for s in get_endpoint('staff')}
    teachers = [t for t in do_get('teachers') if not t['InactiveStatusCode']]
    for tch in teachers:
        staff_id = tch['StaffID1']
        try:
            stf = staff[staff_id]
        except KeyError:
            name = tch['DisplayName']
            click.echo(f'invalid staff id {staff_id} for {name}', err=True)
            continue
        db.session.merge(Teacher(
            id=staff_id,
            email=stf['EmailAddress'],
            name=f"{stf['FirstName']} {stf['LastName']}",
        ))
    db.session.commit()
    click.echo(f'Imported {len(teachers)} teachers.')

    click.echo('Pulling student info from Aeries...')
    students = {s['StudentID']: s for s in do_get('students')}
    sections = {s['SectionNumber']: s for s in do_get('sections')}
    classes = do_get('classes')
    for klass in filter(lambda k: k['CourseID'] == HOME_COURSE_ID, classes):
        stu = students[klass['StudentID']]
        section = sections[klass['SectionNumber']]
        teacher_id = section['SectionStaffMembers'][0]['StaffID']
        db.session.merge(Student(
            id=stu['StudentID'],
            first_name=stu['FirstName'],
            last_name=stu['LastName'],
            home_teacher_id=teacher_id,
        ))
    click.echo(f'Imported {len(students)} students.')

    db.session.commit()
    click.echo('Success.')


def register_commands(app):
    app.cli.add_command(sync_command)
