from prompts.actions.actions_factory import ActionsFactory

class TestActionsFactory:
    def test_create(self):
        factory = ActionsFactory()
        actions_content = factory.create()
        assert "The selected action " in actions_content
        assert " - look - describe the current room" in actions_content
        assert " - quit - quit the game" in actions_content