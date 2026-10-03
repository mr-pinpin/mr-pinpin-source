import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from timings import ingest, metrics


def event(seq, seconds, event_type, **fields):
    return {"seq": seq, "createdAt": "2026-10-03T09:30:%02d+00:00" % seconds, "type": event_type, **fields}


def snapshot(events):
    return {"cursor": max((e["seq"] for e in events), default=0), "events": events,
            "conversation": {"threadId": "thread", "status": "completed", "activeTurnId": None,
                             "messages": [{"id": "u", "role": "user", "createdAt": "2026-10-03T09:30:00+00:00", "turnId": "turn"},
                                          {"id": "a", "role": "assistant", "createdAt": "2026-10-03T09:30:02+00:00", "turnId": "turn",
                                           "phase": "final_answer", "status": "completed", "text": "Must not save transcript"}]}}


class TimingTest(unittest.TestCase):
    def capture(self, events):
        value = {"messageId": "u", "url": "http://studio", "events": []}
        ingest(value, snapshot(events), "2026-10-03T09:31:00+00:00")
        return value

    def test_exact_sequential_image_and_delivery_timestamps(self):
        capture = self.capture([event(1,0,"message",messageId="u"),
                                event(2,1,"status",status="running"), event(3,2,"delta",messageId="a",delta="secret"),
                                event(4,4,"activity",kind="imageGeneration",status="running"),
                                event(5,14,"activity",kind="imageGeneration",status="completed"),
                                event(6,18,"message",messageId="a"), event(7,20,"status",status="completed")])
        result = metrics(capture)
        self.assertEqual(result["firstVisibleProgressSeconds"],1)
        self.assertEqual(result["firstAssistantTextSeconds"],2)
        self.assertEqual(result["imageGeneration"]["totalSeconds"],10)
        self.assertEqual(result["totalSeconds"],20)
        self.assertEqual(result["otherElapsedSeconds"],10)
        self.assertEqual(result["finalDeliveredSeconds"],18)
        self.assertEqual(result["finalMessageIds"],["a"])
        self.assertNotIn("secret",json.dumps(capture))
        self.assertNotIn("Must not save",json.dumps(capture))

    def test_overlapping_image_calls_not_fabricated(self):
        capture=self.capture([event(1,0,"message",messageId="u"),
                              event(2,2,"activity",kind="imageGeneration",status="running"),
                              event(3,3,"activity",kind="imageGeneration",status="running"),
                              event(4,5,"activity",kind="imageGeneration",status="completed"),
                              event(5,6,"activity",kind="imageGeneration",status="completed")])
        result=metrics(capture)
        self.assertTrue(result["imageGeneration"]["ambiguous"])
        self.assertIsNone(result["imageGeneration"]["totalSeconds"])
        self.assertEqual(result["imageGeneration"]["spans"],[])
        self.assertEqual(result["imageGeneration"]["activeWallSeconds"],4)

    def test_retention_gap_and_partial_history_not_full_image_total(self):
        capture=self.capture([event(8,4,"activity",kind="imageGeneration",status="running"),
                              event(9,14,"activity",kind="imageGeneration",status="completed")])
        result=metrics(capture)
        self.assertEqual(result["eventCoverage"],"partial")
        self.assertEqual(result["imageGeneration"]["spans"][0]["seconds"],10)
        self.assertIsNone(result["imageGeneration"]["totalSeconds"])
        ingest(capture,snapshot([event(12,20,"status",status="completed")]),"now")
        self.assertTrue(capture["eventGap"])

    def test_resume_deduplicates_and_ignores_other_turn(self):
        first=[event(1,0,"message",messageId="u"),event(2,2,"delta",messageId="a",delta="one")]
        capture=self.capture(first)
        later=snapshot(first+[event(3,3,"delta",messageId="a",delta="two"),event(4,18,"message",messageId="a"),event(5,20,"status",status="completed"),event(6,30,"activity",kind="imageGeneration",status="running")])
        later["conversation"]["messages"].append({"id":"u2","role":"user","createdAt":"2026-10-03T09:30:25+00:00","turnId":"turn2"})
        ingest(capture,later,"now")
        self.assertEqual(len([e for e in capture["events"] if e["type"]=="delta"]),1)
        result=metrics(capture)
        self.assertEqual(result["imageGeneration"]["exposedEvents"],0)
        self.assertEqual(result["totalSeconds"],20)


if __name__ == "__main__":
    unittest.main()
