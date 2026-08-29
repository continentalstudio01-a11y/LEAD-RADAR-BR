from app.scoring import calculate_score


def test_missing_site_is_high_opportunity_when_contactable():
    lead = {
        'website': None,
        'phone': '(11) 99999-9999',
        'email': 'contato@example.com',
        'social': {'instagram': 'https://instagram.com/example'},
        'address': 'São Paulo',
        'category': 'amenity:dentist',
        'osm': {'id': 1},
        'audit': {'status': 'sem_site', 'issues': []},
        'web_search': {'result_count': 10, 'official_position': None},
    }
    score, funnel, confidence, reasons = calculate_score(lead)
    assert score >= 55
    assert funnel in ('Meio', 'Fundo')
    assert confidence >= 50
    assert any('Sem site' in r for r in reasons)
