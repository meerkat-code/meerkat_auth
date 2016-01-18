#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
"""
import json
import unittest
from datetime import datetime
from datetime import timedelta
from sqlalchemy import extract

import meerkat_api
import meerkat_abacus.manage as manage
import meerkat_abacus.config as config
import meerkat_abacus.model as model




class MeerkatAPITestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        manage.set_up_everything(
            config.DATABASE_URL,
            True, True, N=500)

        self.app = meerkat_api.app.test_client()
        self.locations = {1: {"name": "Demo"}}
        self.variables = {1: {"name": "Total"}}
    def tearDown(self):
        pass

    def test_index(self):
        """Check the index page loads"""
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'WHO', rv.data)
        
    def test_epi_week(self):
        rv = self.app.get('/epi_week/2015-01-02')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert str(data["epi_week"]) == str(1)
        rv = self.app.get('/epi_week/2015-12-02')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert str(data["epi_week"]) == str(48)

    def test_completeness(self):
        #Need some more testing here
        variable = "tot_1"
        rv = self.app.get('/completeness/{}/4'.format(variable))
        year = datetime.now().year
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert "clinics" in data.keys()
        assert "regions" in data.keys()
        assert "1" in data["clinics"].keys()
        for clinic in data["clinics"]["1"].keys():
            results = meerkat_api.db.session.query(
                model.Data).filter(
                    model.Data.clinic == clinic,
                    extract("year", model.Data.date) == year,
                    model.Data.variables.has_key(variable)
                ).all()
            assert data["clinics"]["1"][clinic]["year"] == len(results)


    def test_epi_week_start(self):
        rv = self.app.get('/epi_week_start/2015/49')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert data["start_date"] == "2015-12-03T00:00:00"

    def test_locations(self):
        """Check locations"""
        rv = self.app.get('/locations')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(data), 11)
    def test_tot_clinics(self):
        """Check tot_clinics"""
        rv = self.app.get('/tot_clinics/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        results = meerkat_api.db.session.query(
            model.Locations).filter(
                model.Locations.case_report == "1").all()
        assert data["total"] == len(results)
        rv = self.app.get('/tot_clinics/2')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert data["total"] == 3
    def test_location(self):
        """Check locations"""
        rv = self.app.get('/location/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], self.locations[1]["name"])

    def test_variable(self):
        """Check locations"""
        rv = self.app.get('/variable/tot_1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(data["name"], self.variables[1]["name"])
        
    def test_variables(self):
        """Check locations"""
        rv = self.app.get('/variables/gender')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        assert "gen_1" in data.keys()
        assert "gen_2" in data.keys()
        self.assertEqual(len(data), 2)

    def test_aggregate(self):
        """Check locations"""
        rv = self.app.get('/aggregate/tot_1/1')
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(rv.status_code, 200)
        results = meerkat_api.db.session.query(
            model.form_tables["case"]).filter(
            model.form_tables["case"].data.contains(
                {"intro./visit_type": 'new'}))
        self.assertEqual(data["value"], len(results.all()))

    def test_aggregate_yearly(self):
        """Test for aggregate Yearly"""
        rv = self.app.get('/aggregate_year/tot_1/1')
        year = datetime.now().year
        rv2 = self.app.get('/aggregate_year/tot_1/1/{}'.format(year))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv2.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        data2 = json.loads(rv2.data.decode("utf-8"))
        self.assertEqual(data, data2)

        results = meerkat_api.db.session.query(
            model.Data).filter(
                extract('year', model.Data.date) == year,
                model.Data.variables.has_key("tot_1")
                )

        self.assertEqual(data["year"],len(results.all()))

    def test_aggregate_category(self):
        """Test for aggregate Category """
        rv = self.app.get('/aggregate_category/gender/1')
        year = datetime.now().year
        rv2 = self.app.get('/aggregate_category/gender/1/{}'.format(year))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv2.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        data2 = json.loads(rv2.data.decode("utf-8"))
        self.assertEqual(data, data2)

        results = meerkat_api.db.session.query(
            model.Data).filter(
                extract('year', model.Data.date) == year,
                model.Data.variables.has_key("gen_2")
                )
        self.assertEqual(data['gen_2']["year"], len(results.all()))
        
    def test_clinics(self):
        rv = self.app.get('/clinics/1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data["features"]),4)

    def test_map(self):
        rv = self.app.get('/map/tot_1')
        year = datetime.now().year
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        self.assertEqual(len(data), 4)
        geo_location = data[0]["geolocation"]
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("tot_1"),
            extract("year", model.Data.date) == year,
            model.Data.geolocation == ",".join(geo_location))
        
        self.assertEqual(data[0]["value"], len(results.all()))
        
    def test_query_variable(self):
        rv = self.app.get('/query_variable/1/gender')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        year = datetime.today().year
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("1"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"]+data["Female"]["total"] ==
               len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("2"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"] == len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("3"),
            extract("year", model.Data.date) == year)
        assert(data["Female"]["total"] == len(results.all()))

    def test_query_variable_location(self):
        """Test with variable = location"""
        year = datetime.today().year
        rv = self.app.get('/query_variable/location:1/gender')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("gen_1"),
            extract("year", model.Data.date) == year)
        assert(data["Male"]["total"] == len(results.all()))
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("gen_2"),
            extract("year", model.Data.date) == year)
        assert(data["Female"]["total"] == len(results.all()))
    def test_query_variable_locations(self):
        """Test with group_by = locations"""
        year = datetime.today().year
        rv = self.app.get('/query_variable/tot_1/locations')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Demo" in data)
        assert("Clinic 1" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.region == 2,
            model.Data.variables.has_key("tot_1"),
            extract("year", model.Data.date) == year)
        assert(data["Region 1"]["total"] == len(results.all()))
    def test_query_variable_dates(self):
        """Test with dates"""
        date_end = datetime.now()
        date_start = date_end - timedelta(days=14)
        rv = self.app.get('/query_variable/tot_1/gender/{}/{}'.format(date_start.isoformat(),date_end.isoformat()))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("tot_1"),
            model.Data.variables.has_key("gen_1"),
            model.Data.date >= date_start,
            model.Data.date < date_end)
        assert data["Male"]["total"] == len(results.all())


    def test_query_category(self):
        """test normal function"""
        year = datetime.today().year
        rv = self.app.get('/query_category/gender/age')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("gen_1"),
            model.Data.variables.has_key("age_5"),
            extract("year", model.Data.date) == year)
        n_results = len(results.all())
        if n_results > 0:
            assert("20-59" in data["Male"])
            assert(data["Male"]["20-59"] == n_results)
        else:
            assert("20-59" not in data["Male"])
            
    def test_query_category_locations(self):
        """Test with locations"""
        year = datetime.today().year
        rv = self.app.get('/query_category/gender/locations')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert("Demo" in data)
        assert("Clinic 1" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.region == 2,
            model.Data.variables.has_key("gen_1"),
            extract("year", model.Data.date) == year)
        n_results = len(results.all())
        if n_results > 0:
            assert("Male" in data["Region 1"])
            assert(data["Region 1"]["Male"] == len(results.all()))
        else:
            assert("Male" not in data["Region 1"])
    def test_query_category_dates(self):
        """test with dates"""
        year = datetime.today().year
        date_end = datetime.now()
        date_start = date_end - timedelta(days=14)
        rv = self.app.get('/query_category/gender/age/{}/{}'.format(date_start.isoformat(),date_end.isoformat()))
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        assert("Female" in data)
        assert("Male" in data)
        results = meerkat_api.db.session.query(model.Data).filter(
            model.Data.variables.has_key("gen_1"),
            model.Data.variables.has_key("age_5"),
            model.Data.date >= date_start,
            model.Data.date < date_end)
        n_results = len(results.all())
        if n_results > 0:
            assert("20-59" in data["Male"])
            assert(data["Male"]["20-59"] == n_results)
        else:
            assert("20-59" not in data["Male"])

    def test_alert(self):
        """test alert"""
        results = meerkat_api.db.session.query(model.Alerts).first()
        rv = self.app.get('/alert/' + results.id)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert data["alerts"]["id"] == results.id
        results = meerkat_api.db.session.query(model.Links)\
                .filter(model.Links.link_def == 1).first()
        rv = self.app.get('/alert/' + results.link_value)
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        print(data)
        assert "links" in data.keys()
        
    def test_aggregate_alert(self):
        """test aggregate_alerts"""
        results = meerkat_api.db.session.query(model.Alerts).all()
        rv = self.app.get('/aggregate_alerts')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert data["total"] == len(results)
        reason = list(data.keys())
        reason.remove("total")
        reason = reason[0]
        tot = 0
        for r in results:
            if str(r.reason) == str(reason):
                tot += 1
        assert tot == sum(data[reason].values())
        rv = self.app.get('/aggregate_alerts?location=11')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).filter(
            model.Alerts.clinic == 11).all()
        assert data["total"] == len(results)

    
    def test_alerts(self):
        """test alerts"""
        rv = self.app.get('/alerts')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).all()
        links = meerkat_api.db.session.query(model.Links).filter(
            model.Links.link_def == 1).all()
        link_ids = []
        for l in links:
            link_ids.append(l.link_value)
        for d in data["alerts"]:
            if d["alerts"]["id"] in link_ids:
                assert "links" in d
            else:
                assert "links" not in d
        
        assert len(data["alerts"]) == len(results)

        rv = self.app.get('/alerts?reason=moh_24')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).filter(
            model.Alerts.reason == "moh_24").all()
        assert len(data["alerts"]) == len(results)

        rv = self.app.get('/alerts?location=11')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).filter(
            model.Alerts.clinic == 11).all()
        assert len(data["alerts"]) == len(results)
        rv = self.app.get('/alerts?location=1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        results = meerkat_api.db.session.query(model.Alerts).all()
        assert len(data["alerts"]) == len(results)
        
    def test_location_tree(self):
        rv = self.app.get('/locationtree')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode("utf-8"))
        assert data["text"] == "Demo"
        nodes = data["nodes"]
        ids = []
        for n in nodes:
            ids.append(n["id"])
        assert 2 in ids
        assert 3 in ids
        assert 4 not in ids
        assert 5 not in ids
        
if __name__ == '__main__':
    unittest.main()
