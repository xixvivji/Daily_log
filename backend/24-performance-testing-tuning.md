# 24. 성능 Test와 JVM·DB Tuning

## 성능 개선의 원칙

```text
목표 정의
→ 측정
→ 병목 가설
→ 한 가지 변경
→ 다시 측정
→ 회귀 확인
```

Metric 없이 설정값을 바꾸는 것은 tuning이 아니라 추측이다.

## 핵심 지표

```text
Latency
→ 요청 하나가 걸린 시간

Throughput
→ 초당 처리 요청 수

Concurrency
→ 동시에 진행 중인 작업 수

Error Rate
→ 실패 비율

Saturation
→ thread, connection, CPU 같은 자원이 한계에 가까운 정도
```

평균은 tail latency를 숨긴다. p50, p95, p99를 함께 본다.

## 목표 예시

```text
정상 traffic 200 RPS
p95 < 300ms
p99 < 800ms
error rate < 1%
30분 유지 시 memory 증가가 안정화
```

Test 전에 실제 SLO와 예상 traffic, 읽기/쓰기 비율을 정한다.

## 성능 Test 종류

```text
Smoke Test
→ 매우 작은 부하에서 script와 기본 동작 확인

Load Test
→ 예상 정상 부하 검증

Stress Test
→ 한계를 넘겨 병목과 실패 형태 확인

Spike Test
→ 갑작스러운 traffic 증가 대응

Soak Test
→ 장시간 실행해 memory leak, connection 누수 확인

Breakpoint Test
→ 처리 한계와 붕괴 지점 탐색
```

## Open Model과 Closed Model

```text
Closed Model
→ 정해진 virtual user가 응답 후 다음 요청
→ server가 느려지면 요청 생성률도 낮아짐

Open Model
→ 일정 arrival rate로 요청 도착
→ 실제 traffic처럼 backlog와 saturation을 드러내기 쉬움
```

목표가 500 RPS라면 virtual user 수만 고정하는 것보다 arrival-rate scenario가 더 적절할 수 있다.

## k6 예시

```javascript
import http from 'k6/http';

export const options = {
  scenarios: {
    api_load: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 200,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<300', 'p(99)<800'],
  },
};

export default function () {
  http.get(`${__ENV.BASE_URL}/api/products/1`);
}
```

Test data 충돌, 인증 token 재사용, client-side bottleneck을 확인한다. 부하 발생기 자체의 CPU와 network가 먼저 한계에 도달할 수 있다.

## Test 환경

```text
production과 유사한 DB 종류와 schema
충분한 데이터 양과 분포
동일한 JVM 옵션과 container limit
비슷한 network latency
외부 API는 통제 가능한 stub 또는 별도 quota
monitoring 활성화
```

운영에서 허가 없이 stress test하지 않는다.

## 병목 분류

```text
CPU-bound
→ CPU 높음, runnable thread 증가, hot method

Memory/GC
→ allocation 증가, GC pause, heap 지속 증가

Thread Pool
→ active max, queue 증가, timeout

Connection Pool
→ pending acquire와 transaction duration 증가

DB
→ slow query, lock wait, high I/O, connection 포화

External API
→ client latency, timeout, retry 증가

Network
→ retransmission, bandwidth, DNS/TLS 지연
```

## JVM 관찰

```text
heap 사용량과 GC 후 baseline
allocation rate
GC pause와 frequency
thread state와 deadlock
CPU hot method
class와 metaspace
direct memory
```

진단 도구:

```bash
jcmd <pid> Thread.print
jcmd <pid> GC.class_histogram
jcmd <pid> GC.heap_dump /tmp/heap.hprof
jcmd <pid> JFR.start name=profile duration=60s filename=/tmp/profile.jfr
```

Heap dump는 크고 process에 부담을 줄 수 있으므로 disk 공간과 운영 영향을 확인한다.

## Thread Pool Tuning

```text
CPU 작업
→ core 수와 작업 특성 기준

Blocking I/O
→ 대기 시간이 많아 더 많은 thread가 필요할 수 있음
→ downstream capacity가 상한
```

Thread를 늘려도 DB connection이 20개면 DB 작업 동시성은 제한된다. Queue가 무제한이면 overload가 latency와 memory로 쌓이므로 bounded queue와 rejection 정책을 둔다.

## Connection Pool Tuning

```text
application instance 수 × pool size
≤ DB가 감당할 전체 connection budget
```

Pool을 크게 하면 query가 빨라지는 것이 아니다. DB에 동시에 더 많은 작업이 몰려 오히려 처리량이 감소할 수 있다.

관찰:

```text
active/idle/pending
acquire time
connection timeout
transaction duration
DB CPU와 lock wait
```

## DB Tuning 순서

```text
N+1과 query 횟수 제거
필요 column과 row만 조회
실행 계획 확인
적절한 index
pagination 방식 개선
transaction과 lock 범위 축소
batch/bulk 처리
그다음 DB parameter 검토
```

DB instance 크기를 먼저 키우면 비효율적인 SQL이 더 큰 비용으로 남을 수 있다.

## Cache 성능 검증

```text
hit ratio
miss latency
eviction
hot key
memory usage
Redis command latency
cache 장애 시 DB 부하
```

높은 hit ratio만 목표로 하면 stale data와 memory 비용이 커질 수 있다.

## Metric Cardinality

`memberId`, `orderId`, URL 전체를 metric tag로 넣으면 시계열 수가 폭증한다.

```text
좋은 tag → method, route template, status group, provider
위험한 tag → user ID, raw URL, request ID
```

개별 요청 식별은 log와 trace를 사용한다.

## 변경 결과 판단

```text
같은 workload와 test data
warm-up 이후 비교
여러 번 실행해 변동 확인
latency뿐 아니라 error와 resource 비교
다른 endpoint 회귀 확인
비용 변화 확인
```

## 흔한 실수

```text
평균 latency만 봄
너무 작은 DB로 test
local laptop 결과를 production capacity로 해석
JIT warm-up 전후를 섞음
test 중 autoscaling으로 조건이 계속 변함
외부 API를 실제로 무제한 호출
병목을 확인하지 않고 thread와 heap부터 늘림
```

## 공식 참고 자료

- [Grafana k6 Scenarios](https://grafana.com/docs/k6/latest/using-k6/scenarios/)
- [Grafana k6 Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/)
- [Micrometer Histograms and Percentiles](https://docs.micrometer.io/micrometer/reference/concepts/histogram-quantiles.html)
- [Oracle jcmd](https://docs.oracle.com/en/java/javase/24/docs/specs/man/jcmd.html)

## 설명할 때 핵심 문장

```text
성능 tuning은 목표를 정하고 production과 유사한 workload에서 측정한 뒤 가장 큰 병목을 하나씩 제거하는 과정이다.
p95와 p99 latency, throughput, error rate, saturation을 함께 봐야 한다.
```
