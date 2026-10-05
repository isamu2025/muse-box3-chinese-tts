#include "muse_tts_fake_sdk.h"
#include "muse_tts.h"
#include <cassert>
#include <cstdio>
std::atomic<int> test_allocations{0};
std::atomic<size_t> test_peak{0};
std::string test_mode,test_body;
static void cleanup_wait() {
    for(int i=0;i<3000 && (muse_tts_busy()||test_allocations);++i) std::this_thread::sleep_for(std::chrono::milliseconds(1));
    assert(!muse_tts_busy() && test_allocations==0);
}
int main(int argc,char **argv) {
    assert(argc==2); test_mode=argv[1];
    assert(!muse_tts_begin("") && !muse_tts_begin(nullptr));
    std::string text=test_mode=="utf8" ? std::string(4093,'x')+"\xe4\xbd" : "hello Muse";
    auto r=muse_tts_begin(text.c_str()); assert(r);
    if(test_mode=="cancel") {
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        assert(muse_tts_busy()); assert(!muse_tts_begin("another request"));
        muse_tts_close(&r); assert(!r); cleanup_wait(); return 0;
    }
    bool ok=false,finished=false;
    std::vector<uint8_t> received;
    for(int i=0;i<5000 && !finished;++i) {
        uint8_t block[733]; size_t n=muse_tts_read(r,block,sizeof(block));
        received.insert(received.end(),block,block+n);
        finished=muse_tts_finished(r,&ok);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    assert(finished);
    bool failure=test_mode=="badhttp"||test_mode=="badtype"||test_mode=="timeout"||test_mode=="truncated";
    assert(ok!=failure);
    if(!failure) {
        assert(received.size()==(test_mode=="large"?256*1024:7000));
        for(size_t i=0;i<received.size();++i) assert(received[i]==i%251);
    }
    assert(test_peak<=8192);
    if(test_mode=="utf8") assert(test_body==std::string(4093,'x'));
    muse_tts_close(&r); assert(!r); cleanup_wait();
    puts("ok");
}
