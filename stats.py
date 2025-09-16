def read_csv_column(col_name):
    """Return list of floats from the given column in data_log.csv."""
    values = []
    with open("data_log.csv", "r") as f:
        # Read header
        header = f.readline().strip().split(",")
        try:
            col_index = header.index(col_name)
        except ValueError:
            return []  # Column not found
        for line in f:
            parts = line.strip().split(",")
            if len(parts) <= col_index:
                continue
            try:
                values.append(float(parts[col_index]))
            except ValueError:
                continue
    return values


def average(col_name):
    values = read_csv_column(col_name)
    total_readings = len(values)
    minutes_in_day = 24 * 60

    if total_readings < 1:
        return None
    elif total_readings < minutes_in_day:
        return sum(values) / total_readings
    else:
        last_24h = values[-minutes_in_day:]
        return sum(last_24h) / len(last_24h)


def low(col_name):
    values = read_csv_column(col_name)
    total_readings = len(values)
    minutes_in_day = 24 * 60

    if total_readings < 1:
        return None
    elif total_readings < minutes_in_day:
        return min(values)
    else:
        return min(values[-minutes_in_day:])


def high(col_name):
    values = read_csv_column(col_name)
    total_readings = len(values)
    minutes_in_day = 24 * 60

    if total_readings < 1:
        return None
    elif total_readings < minutes_in_day:
        return max(values)
    else:
        return max(values[-minutes_in_day:])



