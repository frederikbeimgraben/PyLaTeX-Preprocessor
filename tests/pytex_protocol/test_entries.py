from pytex_protocol.entries import ActionItem, Deadline, Decision, Timestamp, Vote


def test_decision_box_has_label_and_gavel():
    out = Decision("Antrag angenommen").rendered
    assert "Beschluss" in out
    assert "gavel" in out
    assert "Antrag angenommen" in out


def test_deadline_appends_due_date():
    out = Deadline("Unterlagen einreichen", due="30.06.2026").rendered
    assert "Frist" in out
    assert "bis 30.06.2026" in out
    assert "hourglass" in out


def test_action_item_renders_assignee_and_due():
    out = ActionItem("Doku schreiben", who="C. Schmidt", due="nächste Sitzung").rendered
    assert "Aufgabe" in out
    assert "Zuständig: C. Schmidt" in out
    assert "Frist: nächste Sitzung" in out


def test_action_item_without_meta():
    out = ActionItem("Nur Text").rendered
    assert "Aufgabe" in out
    assert "Zuständig" not in out


def test_vote_reuses_voting_results():
    out = Vote(yes=5, no=1, abstain=0, body="Antrag X").rendered
    assert "vote-yea" in out
    assert "Antrag X" in out


def test_timestamp_is_blue_and_bold():
    out = Timestamp("18:30").rendered
    assert "hanblue" in out
    assert "18:30" in out
