import os

import click
import requests

from pushpull import errors
from pushpull.app import app
from pushpull.model import Assignment, Period, Student, Teacher, session


AERIES_CERT = os.getenv('AERIES_CERT')
AERIES_API_BASE = os.getenv('AERIES_API_BASE')

SCHOOL_ID = 1
HOME_COURSE_ID = '2604'


def get_endpoint(*components):
    assert AERIES_CERT
    headers = {'AERIES-CERT': AERIES_CERT}
    endpoint = '/'.join(map(str, components))
    url = f'{AERIES_API_BASE}/api/v5/{endpoint}'
    return requests.get(url, headers=headers).json()


def school_endpoint(school_code, endpoint):
    return endpoint(f'schools/{school_code}/{endpoint}')


@app.cli.command('dump')
def dump_command():
    """Debugging command which dumps data from Aeries into JSON files."""
    import json
    import os
    do_get = lambda e: get_endpoint('schools', SCHOOL_ID, e)
    staff = get_endpoint('staff')
    teachers = do_get('teachers')
    students = do_get('students')
    sections = do_get('sections')
    classes = do_get('classes')
    dump = lambda d, p: json.dump(d, open(os.path.expanduser(p), 'w'))
    dump(staff, '/tmp/staff.json')
    dump(teachers, '/tmp/teachers.json')
    dump(students, '/tmp/students.json')
    dump(sections, '/tmp/sections.json')
    dump(classes, '/tmp/classes.json')


@app.cli.command('sync')
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
        session.merge(Teacher(
            id=staff_id,
            email=stf['EmailAddress'],
            name=f"{stf['FirstName']} {stf['LastName']}",
        ))
    session.commit()
    click.echo(f'Imported {len(teachers)} teachers.')

    # Skip invalid teacher IDs
    teachers: list[Teacher] = session.query(Teacher).all()

    click.echo('Pulling student info from Aeries...')
    students = {s['StudentID']: s for s in do_get('students')}
    sections = {s['SectionNumber']: s for s in do_get('sections')}
    classes = do_get('classes')
    for klass in filter(lambda k: k['CourseID'] == HOME_COURSE_ID, classes):
        stu = students[klass['StudentID']]
        section = sections[klass['SectionNumber']]
        try:
            period = Period.get_by_name(section['Period'])
            teacher_id = section['SectionStaffMembers'][0]['StaffID']
            Teacher.get(teacher_id)
        except (KeyError, IndexError, errors.NoSuchResource) as e:
            click.echo(f'invalid section {section["SectionNumber"]}: {e}', err=True)
            continue
        student = Student(
            id=stu['StudentID'],
            first_name=stu['FirstName'],
            last_name=stu['LastName'],
        )
        session.merge(student)
        session.merge(Assignment(
            student_id=student.id,
            period_id=period.id,
            teacher_id=teacher_id,
        ))
    click.echo(f'Imported {len(students)} students.')

    session.commit()
    click.echo('Success.')
