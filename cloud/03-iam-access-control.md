# 03. IAM과 권한 관리

## IAM이 하는 일

IAM은 AWS resource에 누가 어떤 작업을 어떤 조건에서 할 수 있는지 제어한다.

```text
Authentication
→ 요청한 주체가 누구인지 확인

Authorization
→ 그 주체가 특정 action을 특정 resource에 수행할 수 있는지 평가
```

AWS Console, CLI, SDK의 작업은 결국 AWS API request이며 IAM authorization 평가를 거친다.

## Principal

AWS에 요청을 보내는 주체다.

```text
Root User
IAM User
IAM Role Session
Federated User
AWS Service Principal
다른 AWS Account
```

`EC2 instance` 자체에 영구 access key를 넣는 대신 EC2가 IAM Role을 assume한 session principal로 요청하게 한다.

## Root User

Account를 만들 때 생성되는 최고 권한 identity다.

기본 원칙:

```text
MFA 활성화
일상 작업에 사용하지 않음
Root access key 생성 금지
Root email과 복구 수단 보호
Root 사용 event monitoring
Root만 가능한 제한된 작업에만 사용
```

Root user를 admin IAM user와 혼동하면 안 된다. Admin도 policy로 권한을 받은 identity지만 root에는 account 수준의 특별 작업이 있다.

## IAM User

특정 사람이나 application을 위한 장기 identity다.

```text
Console password
Access key ID / Secret access key
```

Access key는 장기 credential이므로 유출과 rotation 부담이 있다. 사람의 access는 IAM Identity Center와 federation, workload는 IAM Role과 temporary credential을 우선한다.

## IAM Group

IAM User를 묶어 permission을 적용한다.

```text
Developers Group
→ 개발 환경 조회·배포 권한

Auditors Group
→ 읽기와 감사 권한
```

Group은 다른 Group을 포함하지 않고 Role처럼 assume하지 않는다. 사람 권한 관리에 사용한다.

## IAM Role

고정 password나 access key가 없는 assumable identity다.

```text
EC2 Role
→ application이 S3 접근

Lambda Execution Role
→ function이 DynamoDB 접근

Cross-Account Role
→ 다른 account 사용자가 assume

CI/CD Role
→ GitHub Actions가 OIDC federation으로 assume
```

Role을 assume하면 AWS STS가 제한된 수명의 temporary credential을 발급한다.

```text
AccessKeyId
SecretAccessKey
SessionToken
Expiration
```

## Role의 두 Policy

```text
Trust Policy
→ 누가 이 Role을 assume할 수 있는가?

Permissions Policy
→ Role을 assume한 session이 무엇을 할 수 있는가?
```

Trust policy 예:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
```

이 설정만으로 S3 권한이 생기지는 않는다. 별도의 permission policy가 필요하다.

## Policy 구조

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadApplicationFiles",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::my-app-bucket/config/*"],
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/Environment": "prod"
        }
      }
    }
  ]
}
```

```text
Effect
→ Allow 또는 Deny

Action
→ 허용·거부할 AWS API action

Resource
→ 대상 ARN

Condition
→ IP, tag, encryption, MFA 등 추가 조건
```

`Action: *`, `Resource: *`는 편하지만 blast radius가 크다. 필요한 action과 resource 범위를 좁힌다.

## Identity-Based Policy

User, Group, Role에 붙여 해당 identity의 권한을 정의한다.

```text
Member API Role
→ 특정 S3 prefix read
→ 특정 SQS queue send
→ 특정 secret read
```

AWS Managed Policy는 편리하지만 범위가 넓고 AWS가 변경할 수 있다. 업무에 필요한 최소 권한은 customer managed policy로 통제할 수 있다.

## Resource-Based Policy

Resource 자체에 붙어 어떤 principal이 접근 가능한지 정의한다.

```text
S3 Bucket Policy
SQS Queue Policy
SNS Topic Policy
KMS Key Policy
Role Trust Policy
```

Cross-account 접근에서는 요청 주체의 identity policy와 대상 resource policy 관계를 함께 봐야 한다.

## Policy 평가 기본 원리

```text
기본값: Implicit Deny
→ 명시적 Allow가 필요

Explicit Allow
→ 적용되는 policy가 허용

Explicit Deny
→ 다른 Allow보다 우선
```

단순화한 흐름:

```text
요청 인증
→ 적용 가능한 policy 수집
→ Explicit Deny 확인
→ 필요한 Allow 확인
→ permissions boundary, SCP, session policy 제한 확인
→ Allow 또는 Deny
```

`AdministratorAccess`가 있어도 Organizations SCP가 action을 막거나 resource policy에 explicit deny가 있으면 거부될 수 있다.

## Least Privilege

업무에 필요한 최소 action, resource, condition만 허용한다.

나쁜 예:

```json
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
}
```

개선 방향:

```text
GetObject만 허용
특정 bucket과 prefix로 제한
특정 VPC endpoint 또는 source 조건
암호화된 object만 upload
필요한 session 시간 제한
```

처음부터 완벽한 최소 권한을 만들기 어려우면 개발 중 임시 권한을 사용하더라도 CloudTrail과 Access Advisor를 바탕으로 줄이고 production 전에 검토한다.

## EC2 Instance Role

Spring Boot가 S3를 읽는다고 가정한다.

나쁜 방식:

```text
application.yml에 access key 저장
Git 또는 image에 secret 포함
```

좋은 흐름:

```text
EC2에 IAM Role 연결
→ Instance Metadata를 통해 temporary credential 제공
→ AWS SDK default credential provider가 credential 획득
→ 자동 rotation
```

Application code에 access key를 넣지 않는다.

## Instance Profile

EC2에 IAM Role을 전달하기 위한 container 역할을 한다. Console에서는 Role을 EC2에 연결하는 것처럼 보이지만 내부적으로 instance profile이 사용된다.

```text
IAM Role
→ permission과 trust

Instance Profile
→ EC2에 Role을 연결하는 resource
```

## Cross-Account Role

Development account의 engineer가 Production account Role을 assume하는 흐름:

```text
Dev identity policy
→ sts:AssumeRole 허용

Prod Role trust policy
→ Dev account principal 신뢰

Prod Role permission policy
→ production에서 가능한 작업 제한
```

장기 production access key를 공유하는 것보다 session 기반 접근과 audit가 쉽다.

## Service Control Policy

AWS Organizations에서 account 또는 OU에 적용할 수 있는 최대 권한 guardrail이다.

```text
SCP가 Allow
→ 그 자체로 IAM permission을 부여하지 않음

SCP가 Deny 또는 허용 범위 밖
→ account의 IAM policy가 Allow해도 차단
```

예:

```text
특정 Region 밖 resource 생성 금지
CloudTrail 비활성화 금지
Root user action 제한
```

## Permissions Boundary

IAM User나 Role이 가질 수 있는 최대 permission 범위를 제한한다.

```text
Developer가 Role 생성 가능
하지만 Boundary 밖 권한은 새 Role에 부여 불가
```

Boundary도 권한을 직접 주지 않는다. Identity policy가 허용하고 Boundary 범위 안이어야 한다.

## Condition 활용

```text
aws:MultiFactorAuthPresent
aws:SourceIp
aws:PrincipalArn
aws:ResourceTag
aws:RequestTag
aws:SecureTransport
```

예를 들어 S3 bucket policy에서 HTTPS가 아닌 요청을 explicit deny할 수 있다.

Condition key 지원 여부와 request context는 서비스와 action마다 다르므로 공식 문서를 확인한다.

## Credential 우선순위와 유출

AWS SDK는 environment variable, profile, container/instance role 등 여러 credential source를 확인할 수 있다.

```text
Local 개발
→ IAM Identity Center 또는 short-lived profile

EC2/ECS/Lambda
→ workload Role

GitHub Actions
→ OIDC federation으로 Role assume
```

Access key가 유출되면 Git에서 지우는 것만으로 부족하다.

```text
즉시 key 비활성화·삭제
CloudTrail에서 사용 내역 확인
영향 resource와 data 조사
새 credential 발급
원인과 재발 방지 조치
```

## IAM과 Application 권한 차이

```text
IAM
→ AWS resource와 API 권한

Spring Security
→ application 사용자와 API 권한
```

사용자가 게시글을 수정할 수 있는지는 Spring Security와 domain rule이고, application이 S3 object를 읽을 수 있는지는 IAM이다.

## 권한 오류 분석

```text
1. 실제 Principal ARN 확인
2. 요청 Action 확인
3. Resource ARN 확인
4. Identity policy Allow 확인
5. Resource policy 확인
6. Explicit Deny 확인
7. Permissions Boundary 확인
8. SCP 확인
9. KMS Key Policy 같은 별도 권한 확인
10. CloudTrail event 확인
```

S3 object 접근에는 S3 권한 외에 사용한 KMS key 복호화 권한도 필요할 수 있다.

## 흔한 실수

```text
Root user로 일상 작업
Root access key 생성
EC2 안에 long-term access key 저장
모든 Role에 AdministratorAccess
Trust policy Principal을 과도하게 개방
Resource와 Action에 무조건 wildcard
개발·운영 account가 같고 권한도 동일
퇴사자와 사용하지 않는 key 방치
권한 오류를 해결하려고 계속 권한만 확대
```

## 첫 IAM 실습

```text
1. Root MFA와 Budget 확인
2. 일상 작업용 federated/admin identity 준비
3. EC2가 assume할 Role 생성
4. 특정 S3 bucket prefix read policy 작성
5. EC2에 Role 연결
6. AWS CLI로 허용 action 성공 확인
7. 허용하지 않은 delete action 실패 확인
8. CloudTrail에서 요청 principal과 event 확인
```

권한이 되는 것뿐 아니라 되면 안 되는 작업이 실제로 거부되는지도 test한다.

## 공식 참고 자료

- [AWS Root User Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/root-user-best-practices.html)
- [IAM Policies and Permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
- [IAM Policy Evaluation Logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
- [Cross-account Policy Evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic-cross-account.html)

## 설명할 때 핵심 문장

```text
IAM은 AWS API 요청의 principal, action, resource, condition을 평가해 권한을 결정한다.
Role은 장기 access key 없이 temporary credential을 제공하므로 AWS workload와 cross-account 접근에 사용한다.
권한은 기본적으로 거부되고 명시적 Allow가 필요하며 Explicit Deny는 Allow보다 우선한다.
Least Privilege는 필요한 action과 resource만 허용하고 실제 사용 기록을 보며 계속 줄이는 과정이다.
```
