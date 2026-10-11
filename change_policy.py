POSITIVE = {'fit', 'positive'}
NEGATIVE = {'injured', 'injury', 'high_negative'}
WATCH = {'watch', 'doubtful', 'rebuild'}

def should_push(change, favorite_player_ids):
    if change.get('playerId') not in favorite_player_ids:
        return False
    if change.get('kind') == 'status_change':
        return change.get('from') != change.get('to')
    if change.get('kind') == 'new_news':
        return change.get('relevance') in {'high_negative','watch','positive'}
    return False
