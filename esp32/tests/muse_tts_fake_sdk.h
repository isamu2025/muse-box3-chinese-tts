#pragma once
#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#define CONFIG_MUSE_LOCAL_TTS_URL "http://192.0.2.10:8765/tts"
#define MALLOC_CAP_SPIRAM 1
#define MALLOC_CAP_8BIT 2
#define pdPASS 1
#define pdMS_TO_TICKS(n) (n)
#define ESP_OK 0
#define ESP_ERR_HTTP_EAGAIN 7007
#define HTTP_METHOD_POST 1
#define HTTP_EVENT_ON_HEADER 1
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
using esp_err_t = int;
struct StaticStreamBuffer_t {};
struct TestQueue {
    size_t capacity;
    std::deque<uint8_t> data;
    std::mutex mutex;
    std::condition_variable changed;
};
using StreamBufferHandle_t = TestQueue *;
extern std::atomic<int> test_allocations;
extern std::atomic<size_t> test_peak;
extern std::string test_mode, test_body;
inline void *heap_caps_malloc(size_t n, int) { auto p=malloc(n); if(p) ++test_allocations; return p; }
inline void heap_caps_free(void *p) { if(p) {--test_allocations; free(p);} }
inline StreamBufferHandle_t xStreamBufferCreateStatic(size_t n, int, uint8_t *, StaticStreamBuffer_t *) {
    auto q=new TestQueue; q->capacity=n-1; return q;
}
inline void vStreamBufferDelete(TestQueue *q) { delete q; }
inline size_t xStreamBufferSend(TestQueue *q, const void *p, size_t n, int wait) {
    std::unique_lock<std::mutex> lock(q->mutex);
    q->changed.wait_for(lock,std::chrono::milliseconds(wait),[&]{return q->data.size()<q->capacity;});
    n=std::min(n,q->capacity-q->data.size());
    auto bytes=static_cast<const uint8_t *>(p);
    q->data.insert(q->data.end(),bytes,bytes+n);
    test_peak.store(std::max(test_peak.load(),q->data.size()));
    return n;
}
inline size_t xStreamBufferReceive(TestQueue *q, void *p, size_t n, int) {
    std::lock_guard<std::mutex> lock(q->mutex);
    n=std::min(n,q->data.size()); auto bytes=static_cast<uint8_t *>(p);
    for(size_t i=0;i<n;++i) {bytes[i]=q->data.front(); q->data.pop_front();}
    q->changed.notify_all(); return n;
}
inline size_t xStreamBufferBytesAvailable(TestQueue *q) {
    std::lock_guard<std::mutex> lock(q->mutex); return q->data.size();
}
inline int xTaskCreatePinnedToCoreWithCaps(void (*f)(void *),const char *,int,void *p,int,void *,int,int) {
    std::thread([=]{f(p);}).detach(); return pdPASS;
}
inline void vTaskDeleteWithCaps(void *) {}
inline int64_t esp_timer_get_time() {
    static std::atomic<int64_t> forced{0};
    if(test_mode=="timeout") return forced.fetch_add(21000000);
    return std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
struct esp_http_client_event_t {int event_id; void *user_data; const char *header_key,*header_value;};
struct esp_http_client_config_t {
    const char *url=nullptr; int method=0,timeout_ms=0,buffer_size=0;
    esp_err_t (*event_handler)(esp_http_client_event_t *)=nullptr;
    void *user_data=nullptr; bool disable_auto_redirect=false;
};
struct TestHttp {esp_http_client_config_t config; std::vector<uint8_t> data; size_t pos=0; int polls=0; std::string body;};
using esp_http_client_handle_t=TestHttp *;
inline TestHttp *esp_http_client_init(const esp_http_client_config_t *c) {
    auto h=new TestHttp; h->config=*c;
    size_t size=test_mode=="large"||test_mode=="cancel" ? 256*1024 : 7000;
    h->data.resize(size); for(size_t i=0;i<size;++i) h->data[i]=i%251;
    return h;
}
inline int esp_http_client_set_header(TestHttp *,const char *,const char *) {return 0;}
inline int esp_http_client_open(TestHttp *,size_t) {return 0;}
inline int esp_http_client_write(TestHttp *h,const char *p,size_t n) {h->body.append(p,n);return n;}
inline int64_t esp_http_client_fetch_headers(TestHttp *h) {
    esp_http_client_event_t ev{HTTP_EVENT_ON_HEADER,h->config.user_data,"Content-Type",test_mode=="badtype"?"text/html":"audio/mpeg"};
    h->config.event_handler(&ev); return 0;
}
inline int esp_http_client_get_status_code(TestHttp *) {return test_mode=="badhttp"?503:200;}
inline void esp_http_client_set_timeout_ms(TestHttp *,int) {}
inline int esp_http_client_read(TestHttp *h,char *p,size_t n) {
    if(test_mode=="timeout" || h->polls++<2) return -ESP_ERR_HTTP_EAGAIN;
    n=std::min(n,h->data.size()-h->pos); memcpy(p,h->data.data()+h->pos,n);h->pos+=n; return n;
}
inline bool esp_http_client_is_complete_data_received(TestHttp *h) {return test_mode!="truncated" && h->pos==h->data.size();}
inline void esp_http_client_close(TestHttp *) {}
inline void esp_http_client_cleanup(TestHttp *h) {test_body=h->body; delete h;}
