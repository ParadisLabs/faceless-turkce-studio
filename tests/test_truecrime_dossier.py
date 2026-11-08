import unittest
from truecrime_dossier import validate_dossier, DossierError


def valid_dossier():
    return {
        "case_title": "Example documented case",
        "jurisdiction": "Example jurisdiction",
        "case_status": "unresolved",
        "as_of_date": "2026-11-08",
        "sources": [
            {"id": "court", "url": "https://court.example/record", "publisher": "Court", "type": "court_record"},
            {"id": "news", "url": "https://news.example/report", "publisher": "Newsroom", "type": "reputable_journalism"},
        ],
        "timeline": [{"date": "2020-01-01", "event": "Public record filed", "source_ids": ["court", "news"]}],
        "claims": [{"text": "The matter remains unresolved", "status": "unresolved", "source_ids": ["court", "news"]}],
        "victim_safety_review": True,
        "editorial_approval": True,
    }


class DossierValidationTests(unittest.TestCase):
    def test_accepts_complete_sourced_dossier(self):
        result = validate_dossier(valid_dossier())
        self.assertTrue(result["valid"])
        self.assertEqual(result["sources"], 2)

    def test_rejects_missing_primary_source(self):
        data = valid_dossier()
        data["sources"][0]["type"] = "reputable_journalism"
        with self.assertRaises(DossierError):
            validate_dossier(data)

    def test_rejects_claim_with_only_one_source(self):
        data = valid_dossier()
        data["claims"][0]["source_ids"] = ["court"]
        with self.assertRaises(DossierError):
            validate_dossier(data)

    def test_rejects_unreviewed_victim_safety(self):
        data = valid_dossier()
        data["victim_safety_review"] = False
        with self.assertRaises(DossierError):
            validate_dossier(data)

    def test_rejects_http_source(self):
        data = valid_dossier()
        data["sources"][0]["url"] = "http://court.example/record"
        with self.assertRaises(DossierError):
            validate_dossier(data)


if __name__ == "__main__":
    unittest.main()
