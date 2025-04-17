import asyncio
from datetime import datetime, timedelta, timezone
from openleadr import OpenADRClient, enable_default_logging

enable_default_logging()

# Keep track of received events to avoid duplicates
seen_event_ids = set()

# In production implementation, data will use charger meter values
async def collect_report_value():
    return 1.23

# Check if an event is expired
def is_event_expired(event):
    interval = event['event_signals'][0]['intervals'][0]
    dtstart = interval['dtstart']
    duration = interval['duration']
    dtend = dtstart + duration
    return dtend < datetime.now(timezone.utc)

# Handle DR events
async def handle_event(event):
    event_id = event['event_descriptor']['event_id']
    
    # Ignore duplicate
    if event_id in seen_event_ids:
        print(f"[VEN] Ignoring duplicate event: {event_id}")
        return 'optOut'
    
    # Ignore expired
    if is_event_expired(event):
        print(f"[VEN] Ignoring expired event: {event_id}")
        return 'optOut'
    
    seen_event_ids.add(event_id)

    # Notify property managers
    signal = event['event_signals'][0]['signal_payload']
    message = f"[VEN] New DR Event Received:\nID: {event_id}\nSignal: {signal}"
    
    # Using Twilio and Sendgrid
    # Opt-in button in text/email link will send new charging profiles
    send_email_to_property_manager(subject="PlugOp DR Event", body=message)
    send_text_to_property_manager(message)

    # Respond to event (custom logic)
    return 'optIn'  # or 'optOut' based on context

# VEN config with TLS Setup
client = OpenADRClient(
    ven_name='ven123',
    vtn_url='http://localhost:8080/OpenADR2/Simple/2.0b',
    # cert='/path/to/cert.pem',  # Uncomment if using HTTPS + certs
    # key='/path/to/key.pem'
)

# Report config
client.add_report(
    callback=collect_report_value,
    resource_id='device001',
    measurement='voltage',
    sampling_rate=timedelta(seconds=10)
)

# Register event handler
client.add_handler('on_event', handle_event)

# Start the client
loop = asyncio.get_event_loop()
loop.create_task(client.run())
loop.run_forever()
