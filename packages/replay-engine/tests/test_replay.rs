use capsule_replay::archive::CapsuleArchive;
use capsule_replay::Replayer;
use std::io::Write;
use tempfile::NamedTempFile;

fn build_minimal_capsule() -> Vec<u8> {
    use std::io::Cursor;

    let session_json = serde_json::json!({
        "session_id": "ses_test001",
        "agent_name": "test-agent",
        "started_at": "2026-05-27T10:00:00Z",
        "status": "failed",
        "step_count": 1,
        "tags": [],
        "user_metadata": {}
    });

    let event_json = serde_json::json!({
        "event_id": "evt_001",
        "session_id": "ses_test001",
        "step_index": 0,
        "event_type": "llm_call",
        "timestamp": "2026-05-27T10:00:01Z",
        "duration_ms": 123.0,
        "payload": {
            "provider": "openai",
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "test"}]
        }
    });

    let manifest_json = serde_json::json!({
        "capsule_version": "1.0",
        "format_spec_url": "https://capsule-five-delta.vercel.app/spec/v1.0",
        "created_at": "2026-05-27T10:00:00Z",
        "session_id": "ses_test001",
        "integrity": {
            "algorithm": "sha256",
            "events_hash": "",
            "cassettes_hash": "",
            "snapshots_hash": ""
        },
        "compression": { "algorithm": "zstd", "level": 3 },
        "encryption": { "enabled": false },
        "producer": {
            "sdk_name": "capsule-python",
            "sdk_version": "0.1.0",
            "platform": "test",
            "python_version": "3.11.0"
        }
    });

    // Build tar in memory
    let mut tar_buf = Vec::new();
    {
        let mut builder = tar::Builder::new(&mut tar_buf);

        let add_file = |builder: &mut tar::Builder<&mut Vec<u8>>, name: &str, data: &[u8]| {
            let mut header = tar::Header::new_gnu();
            header.set_size(data.len() as u64);
            header.set_mode(0o644);
            header.set_cksum();
            builder.append_data(&mut header, name, data).unwrap();
        };

        let session_bytes = session_json.to_string().into_bytes();
        add_file(&mut builder, "session.json", &session_bytes);

        let event_bytes = event_json.to_string().into_bytes();
        add_file(&mut builder, "events/0001-llm_call.json", &event_bytes);

        let manifest_bytes = manifest_json.to_string().into_bytes();
        add_file(&mut builder, "manifest.json", &manifest_bytes);

        builder.finish().unwrap();
    }

    // Compress with zstd
    zstd::encode_all(std::io::Cursor::new(&tar_buf), 3).unwrap()
}

#[test]
fn test_load_minimal_capsule() {
    let data = build_minimal_capsule();
    let archive = CapsuleArchive::from_bytes(&data).unwrap();
    assert_eq!(archive.session.session_id, "ses_test001");
    assert_eq!(archive.session.agent_name, "test-agent");
    assert_eq!(archive.events.len(), 1);
}

#[test]
fn test_replayer_from_bytes() {
    let data = build_minimal_capsule();
    let replayer = Replayer::from_bytes(&data).unwrap();
    assert_eq!(replayer.session_id(), "ses_test001");
    assert_eq!(replayer.step_count(), 1);
}

#[test]
fn test_replay_returns_all_events() {
    let data = build_minimal_capsule();
    let replayer = Replayer::from_bytes(&data).unwrap();
    let result = replayer.replay().unwrap();
    assert_eq!(result.step_count, 1);
    assert_eq!(result.replayed_events[0].event_type, "llm_call");
}

#[test]
fn test_replayer_from_file() {
    let data = build_minimal_capsule();
    let mut tmp = NamedTempFile::new().unwrap();
    tmp.write_all(&data).unwrap();
    let replayer = Replayer::from_file(tmp.path()).unwrap();
    assert_eq!(replayer.step_count(), 1);
}

#[test]
fn test_branch_context_out_of_range_errors() {
    let data = build_minimal_capsule();
    let replayer = Replayer::from_bytes(&data).unwrap();
    let result = replayer.branch_context(99);
    assert!(result.is_err());
}
