#![no_std]
#![no_main]

use aya_bpf::{macros::kprobe, programs::ProbeContext};
use aya_log_ebpf::info;

#[kprobe]
pub fn latinject(ctx: ProbeContext) -> u32 {
    match try_latinject(ctx) {
        Ok(ret) => ret,
        Err(ret) => ret,
    }
}

fn try_latinject(ctx: ProbeContext) -> Result<u32, u32> {
    info!(&ctx, "function blk_mq_start_request called");
    Ok(0)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    unsafe { core::hint::unreachable_unchecked() }
}
