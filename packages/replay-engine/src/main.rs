//! capsule-replay CLI binary.

use capsule_replay::Replayer;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: capsule-replay <path-to.capsule> [--branch <step>]");
        std::process::exit(1);
    }

    let path = PathBuf::from(&args[1]);

    match Replayer::from_file(&path) {
        Err(e) => {
            eprintln!("Error loading capsule: {e}");
            std::process::exit(1);
        }
        Ok(replayer) => {
            println!("Session: {}", replayer.session_id());
            println!("Steps:   {}", replayer.step_count());

            match replayer.replay() {
                Ok(result) => {
                    println!("Replayed {} events successfully.", result.step_count);
                }
                Err(e) => {
                    eprintln!("Replay failed: {e}");
                    std::process::exit(1);
                }
            }
        }
    }
}
