from src.services.chat_manager import ChatManager


def make(tmp_path):
    return ChatManager(store_path=str(tmp_path / "chats.json"), log=False)


def test_create_rename_delete(tmp_path):
    cm = make(tmp_path)
    a = cm.create_new_chat()
    b = cm.create_new_chat()
    assert cm.current_chat == b
    assert cm.rename_chat(a, "  Work ")
    assert cm.chats[a]["name"] == "Work"
    assert not cm.rename_chat(a, "   ")
    assert cm.delete_chat(b)
    assert cm.current_chat == a
    assert not cm.delete_chat("missing")


def test_add_message_autocreates_chat(tmp_path):
    cm = make(tmp_path)
    m = cm.add_message("user", "hello there")
    assert cm.current_chat and m["tokens"] == 2
    assert cm.get_messages()[-1]["message"] == "hello there"


def test_build_messages_with_and_without_context(tmp_path):
    cm = make(tmp_path)
    cm.add_message("user", "hi")
    cm.add_message("assistant", "hello")
    with_ctx = cm.build_messages("next", system_prompt="be nice")
    assert [m["role"] for m in with_ctx] == ["system", "user", "assistant", "user"]
    cm.toggle_context(False)
    assert cm.build_messages("next") == [{"role": "user", "content": "next"}]


def test_context_respects_token_budget(tmp_path):
    cm = make(tmp_path)
    cm.max_history_tokens = 5
    for i in range(10):
        cm.add_message("user", f"msg {i} a b")  # 4 tokens each
    msgs = cm.build_messages("now")
    assert len(msgs) == 2  # one history message fits, plus the new one
    assert msgs[0]["content"] == "msg 9 a b"


def test_persistence(tmp_path):
    cm = make(tmp_path)
    cid = cm.create_new_chat("Saved")
    cm.add_message("user", "remember me")
    again = make(tmp_path)
    assert again.current_chat == cid
    assert again.get_messages()[0]["message"] == "remember me"


def test_corrupt_store_is_ignored(tmp_path):
    (tmp_path / "chats.json").write_text("{not json")
    assert make(tmp_path).chats == {}


def test_export_import(tmp_path):
    cm = make(tmp_path)
    cid = cm.create_new_chat("X")
    cm.add_message("user", "hi")
    path = cm.export_chat(cid, export_dir=str(tmp_path / "exp"))
    new_id = cm.import_chat(path)
    assert new_id != cid and cm.get_messages(new_id)[0]["message"] == "hi"
