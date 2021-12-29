import json

import requests


class GoogleForms:
    def __init__(self, form_id):
        self.form_id = form_id
        self.url = "https://docs.google.com/forms/d/e/{}/viewform".format(form_id)
        self.form_data = {}
        self.form_data_keys = []
        self.form_data_values = []

    def add_form_data(self, key, value):
        self.form_data_keys.append(key)
        self.form_data_values.append(value)

    def send_form_data(self):
        for key, value in zip(self.form_data_keys, self.form_data_values):
            self.form_data[key] = value
        self.form_data["entry.1855274938"] = self.url
        self.form_data["submit"] = "Submit"
        return self.form_data

    def send_form(self):
        self.send_form_data()
        r = requests.post(self.url, data=self.form_data)
        return r.text

    def get_form_data(self):
        return self.form_data

    def get_form_data_keys(self):
        return self.form_data_keys

    def get_form_data_values(self):
        return self.form_data_values

    def get_url(self):
        return self.url

    def get_form_id(self):
        return self.form_id

    def get_form_data_length(self):
        return len(self.form_data_keys)

    def run(self):
        self.send_form()

    def __str__(self):
        return "GoogleForms(form_id={}, url={}, form_data={}, form_data_keys={}, form_data_values={})".format(
            self.form_id,
            self.url,
            self.form_data,
            self.form_data_keys,
            self.form_data_values,
        )

    def __repr__(self):
        return self.__str__()

    def __del__(self):
        print("GoogleForms object deleted")

    def __call__(self):
        return self.__str__()

    def __len__(self):
        return self.get_form_data_length()

    def __getitem__(self, key):
        return self.form_data[key]

    def __setitem__(self, key, value):
        self.form_data[key] = value

    def __delitem__(self, key):
        del self.form_data[key]

    def __iter__(self):
        return iter(self.form_data)

    def __contains__(self, item):
        return item in self.form_data

    def __eq__(self, other):
        return self.form_data == other.form_data

    def __ne__(self, other):
        return self.form_data != other.form_data

    def __gt__(self, other):
        return self.form_data > other.form_data

    def __ge__(self, other):
        return self.form_data >= other.form_data

    def __lt__(self, other):
        return self.form_data < other.form_data

    def __le__(self, other):
        return self.form_data <= other.form_data

    def __hash__(self):
        return hash(self.form_data)

    def __bool__(self):
        return bool(self.form_data)

    def __nonzero__(self):
        return bool(self.form_data)
