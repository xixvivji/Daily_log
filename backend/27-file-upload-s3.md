# 27. 파일 업로드와 Amazon S3 설계

## 파일 업로드의 두 가지 구조

### Backend 경유 업로드

```text
Client
→ multipart/form-data
→ Spring Backend
→ S3
```

장점:

```text
인증과 검증 흐름이 단순함
backend가 file 내용을 직접 검사 가능
작은 file 구현에 적합
```

단점:

```text
backend network와 memory 사용 증가
큰 file에서 request timeout 위험
application instance 확장 비용 증가
```

### Presigned URL 직접 업로드

```text
1. Client가 backend에 업로드 권한 요청
2. Backend가 object key와 presigned PUT URL 발급
3. Client가 S3에 직접 업로드
4. Client가 완료를 알리거나 event로 완료 확인
```

presigned URL은 AWS credential을 client에 주지 않고 제한된 시간 동안 특정 object 작업을 허용한다.

장점:

```text
file binary가 backend를 통과하지 않음
큰 file에서 application 부하 감소
client가 S3로 직접 전송
```

단점:

```text
발급과 실제 업로드 사이 상태 관리 필요
업로드 완료 여부 별도 확인 필요
content type과 size 검증을 여러 단계에서 수행
미완료 object 정리 정책 필요
```

## DB에는 File 자체를 저장하지 않는다

일반적으로 DB에는 metadata와 object key를 저장한다.

```text
file_object
────────────────────
id
owner_id
bucket
object_key
original_name
content_type
size
checksum
status
created_at
```

S3 URL 전체를 저장하기보다 bucket과 key를 저장하면 domain 변경, CDN 적용, presigned download 전환에 유리하다.

```text
원본 이름
→ 사용자에게 보여줄 metadata

object key
→ server가 생성한 충돌 없는 저장 식별자
```

사용자가 보낸 filename을 그대로 key로 사용하지 않는다. path traversal, 덮어쓰기, 특수문자와 개인정보 노출 문제가 생길 수 있다.

```text
uploads/{memberId}/{uuid}
```

## 상태 모델

presigned upload는 DB row 생성과 S3 upload가 하나의 transaction이 아니다.

```text
PENDING
→ UPLOADED
→ VERIFIED
→ AVAILABLE

실패 또는 만료
→ ABORTED
```

권장 흐름:

```text
1. PENDING metadata 생성
2. presigned URL 발급
3. client upload
4. backend가 HeadObject로 size와 metadata 확인
5. VERIFIED 또는 AVAILABLE 전환
6. 오래된 PENDING object와 row 정리
```

client가 “업로드 완료”라고 보냈다는 사실만 믿지 않고 S3 object 존재와 예상 metadata를 확인한다.

## Presigned URL 발급 예시

AWS SDK for Java 2.x의 `S3Presigner`를 사용한다.

```java
PutObjectRequest putObject = PutObjectRequest.builder()
    .bucket(bucket)
    .key(objectKey)
    .contentType(contentType)
    .build();

PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
    .signatureDuration(Duration.ofMinutes(10))
    .putObjectRequest(putObject)
    .build();

PresignedPutObjectRequest result = s3Presigner.presignPutObject(presignRequest);
```

발급할 때 고정한 `Content-Type` 같은 header가 있으면 client가 실제 PUT 요청에도 동일하게 보내야 signature 검증이 성공한다.

## 보안 검증

확장자와 `Content-Type`만 믿으면 안 된다.

```text
허용 확장자
MIME type
실제 file signature 또는 magic number
최대 size
압축 해제 시 최대 크기
악성 code 검사
이미지 decoder 안전성
```

사용자가 올린 HTML이나 SVG를 같은 origin에서 그대로 제공하면 script 실행 위험이 생길 수 있다. 다운로드 응답의 `Content-Type`, `Content-Disposition`, 별도 domain 사용을 검토한다.

bucket은 기본적으로 private으로 두고 공개가 필요한 object만 CloudFront 또는 제한된 policy를 사용한다.

```text
S3 Block Public Access 활성화
application은 IAM Role 사용
필요한 bucket prefix와 action만 허용
access key를 source code에 저장하지 않음
server-side encryption 적용
```

## Multipart Upload

큰 file은 여러 part로 나누어 업로드할 수 있다.

```text
CreateMultipartUpload
→ UploadPart 여러 번
→ CompleteMultipartUpload
```

장점:

```text
실패한 part만 재전송
parallel upload 가능
큰 file 전송 안정성 향상
```

완료되지 않은 multipart upload는 storage 비용을 발생시킬 수 있으므로 lifecycle rule로 정리한다.

## 삭제와 일관성

DB와 S3를 하나의 ACID transaction으로 묶을 수 없다.

```text
DB row 삭제 성공
S3 삭제 실패
```

즉시 양쪽 삭제를 강제하기보다 상태 변경과 재시도 가능한 작업으로 구성할 수 있다.

```text
AVAILABLE
→ DELETE_PENDING
→ S3 삭제
→ DB metadata 삭제 또는 DELETED
```

실패 작업은 scheduler, queue 또는 outbox로 재처리한다.

## Download 전략

```text
Backend streaming
→ 권한 검사를 세밀하게 적용
→ backend bandwidth 사용

Presigned GET URL
→ 짧은 시간 직접 다운로드
→ URL 유출과 만료 시간 고려

CloudFront signed URL 또는 cookie
→ CDN 배포와 접근 제어 결합
```

object key를 안다고 다운로드할 수 있어서는 안 된다. URL 발급 전에 owner와 resource 접근 권한을 확인한다.

## Test와 운영 지표

```text
허용되지 않은 type과 size 거부
다른 회원 object 접근 거부
만료 URL 동작
동일 key 덮어쓰기 방지
PENDING 만료 정리
S3 실패 시 retry와 상태 유지
DB/S3 불일치 탐지
upload 성공률, latency, size 분포
```

LocalStack 같은 대체 환경은 빠른 통합 테스트에 유용하지만 실제 AWS의 IAM, CORS, presigned signature 동작도 별도 환경에서 확인한다.

## 공식 참고 자료

- [AWS SDK for Java 2.x S3](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3.html)
- [AWS SDK for Java Presigned URLs](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/examples-s3-presign.html)
- [Amazon S3 Presigned URL](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)
- [Amazon S3 Multipart Upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)

## 설명할 때 핵심 문장

파일 업로드는 binary 전달뿐 아니라 metadata, 권한, 검증, 상태와 정리 작업까지 포함한다. 큰 파일은 presigned URL로 S3에 직접 보내 application 부하를 줄이고, DB와 S3 사이의 일관성은 상태와 재시도로 관리한다.
