from app.services.tile_loader import TILES, get_tile


def test_tiles_are_loaded():
    assert len(TILES) > 0


def test_general_tile_exists():
    tile = get_tile('general')
    assert tile is not None
    assert isinstance(tile.model, str)
    assert tile.model
