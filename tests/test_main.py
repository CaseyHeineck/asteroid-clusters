from unittest.mock import MagicMock, patch

# --- main() ---
def test_main_instantiates_game_and_calls_run():
    with patch("main.Game") as MockGame:
        mock_instance = MagicMock()
        MockGame.return_value = mock_instance
        from main import main
        main()
        MockGame.assert_called_once()
        mock_instance.run.assert_called_once()
