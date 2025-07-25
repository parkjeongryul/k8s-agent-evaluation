#!/usr/bin/env python3
"""
평가 결과 JSON을 예쁘게 시각화하는 도구
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import argparse

# 색상 코드 (터미널용)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def load_json_results(filepath: str) -> Dict[str, Any]:
    """JSON 결과 파일 로드"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        sys.exit(1)


def color_score(score: float) -> str:
    """점수에 따른 색상 적용"""
    if score >= 0.8:
        return f"{Colors.GREEN}{score:.3f}{Colors.ENDC}"
    elif score >= 0.6:
        return f"{Colors.YELLOW}{score:.3f}{Colors.ENDC}"
    else:
        return f"{Colors.RED}{score:.3f}{Colors.ENDC}"


def print_header(title: str):
    """섹션 헤더 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_metadata(data: Dict[str, Any]):
    """메타데이터 표시"""
    metadata = data.get('evaluation_metadata', data.get('metrics', {}).get('evaluation_metadata', {}))
    
    if metadata:
        print_header("📋 평가 정보")
        print(f"평가 시간: {metadata.get('timestamp', 'N/A')}")
        print(f"평가 방식: {metadata.get('evaluator_used', 'N/A')}")
        print(f"Agent 품질: {metadata.get('agent_quality_level', 'N/A')}")
        print(f"테스트 케이스: {metadata.get('total_test_cases', 'N/A')}개")


def print_overall_metrics(data: Dict[str, Any]):
    """전체 메트릭 표시"""
    metrics = data.get('metrics', {}).get('aggregate', {}).get('overall', {})
    
    if metrics:
        print_header("📊 전체 평가 결과")
        
        # 주요 점수
        print(f"\n{Colors.BOLD}평균 점수:{Colors.ENDC}")
        print(f"  종합 점수: {color_score(metrics.get('avg_overall', 0))}")
        print(f"  정확성:   {color_score(metrics.get('avg_correctness', 0))}")
        print(f"  관련성:   {color_score(metrics.get('avg_relevance', 0))}")
        print(f"  완전성:   {color_score(metrics.get('avg_completeness', 0))}")
        
        # 통계
        print(f"\n{Colors.BOLD}통계 정보:{Colors.ENDC}")
        print(f"  표준편차:  {metrics.get('std_overall', 0):.3f}")
        print(f"  최소점수:  {color_score(metrics.get('min_overall', 0))}")
        print(f"  최대점수:  {color_score(metrics.get('max_overall', 0))}")
        
        # 백분위수
        if 'p50_overall' in metrics:
            print(f"\n{Colors.BOLD}백분위수:{Colors.ENDC}")
            print(f"  25%: {color_score(metrics.get('p25_overall', 0))}")
            print(f"  50%: {color_score(metrics.get('p50_overall', 0))}")
            print(f"  75%: {color_score(metrics.get('p75_overall', 0))}")
            print(f"  90%: {color_score(metrics.get('p90_overall', 0))}")


def print_score_distribution(data: Dict[str, Any]):
    """점수 분포 표시"""
    distribution = data.get('metrics', {}).get('aggregate', {}).get('distribution', {})
    
    if distribution:
        print_header("📈 점수 분포")
        
        max_count = max(distribution.values()) if distribution.values() else 1
        
        for range_key, count in sorted(distribution.items()):
            bar_length = int((count / max_count) * 40)
            bar = '█' * bar_length
            
            # 범위별 색상
            if '0.8-1.0' in range_key:
                color = Colors.GREEN
            elif '0.6-0.8' in range_key:
                color = Colors.YELLOW
            else:
                color = Colors.RED
                
            print(f"  {range_key}: {color}{bar}{Colors.ENDC} {count}")


def print_metrics_by_type(data: Dict[str, Any]):
    """쿼리 타입별 메트릭 표시"""
    by_type = data.get('metrics', {}).get('by_query_type', {})
    
    if by_type:
        print_header("🔍 쿼리 타입별 성능")
        
        # 테이블 헤더
        print(f"\n{'타입':20} {'정확성':>10} {'관련성':>10} {'완전성':>10} {'종합':>10} {'개수':>6}")
        print("-" * 70)
        
        for query_type, metrics in by_type.items():
            print(f"{query_type:20} "
                  f"{color_score(metrics.get('avg_correctness', 0)):>10} "
                  f"{color_score(metrics.get('avg_relevance', 0)):>10} "
                  f"{color_score(metrics.get('avg_completeness', 0)):>10} "
                  f"{color_score(metrics.get('avg_overall', 0)):>10} "
                  f"{metrics.get('count', 0):>6}")


def print_improvement_areas(data: Dict[str, Any]):
    """개선 필요 영역 표시"""
    improvement = data.get('metrics', {}).get('improvement_areas', {})
    
    if improvement:
        print_header("🎯 개선 필요 영역")
        
        areas = improvement.get('areas_needing_improvement', {})
        if areas:
            print(f"\n낮은 성능 비율:")
            for area, ratio in areas.items():
                percentage = ratio * 100
                color = Colors.RED if percentage > 20 else Colors.YELLOW if percentage > 10 else Colors.GREEN
                print(f"  {area}: {color}{percentage:.1f}%{Colors.ENDC}")
        
        print(f"\n가장 많은 문제: {improvement.get('most_common_issue', 'N/A')}")
        print(f"개선 필요 케이스: {improvement.get('low_performing_count', 0)}개 "
              f"({improvement.get('low_performing_percentage', 0):.1f}%)")


def print_detailed_results(data: Dict[str, Any]):
    """상세 결과 표시"""
    results = data.get('results_summary', [])
    
    if results:
        print_header("📝 상세 평가 결과")
        
        # 테이블 헤더
        print(f"\n{'Query ID':15} {'정확성':>8} {'관련성':>8} {'완전성':>8} {'종합':>8}")
        print("-" * 55)
        
        for result in results:
            print(f"{result['query_id']:15} "
                  f"{color_score(result.get('correctness', 0)):>8} "
                  f"{color_score(result.get('relevance', 0)):>8} "
                  f"{color_score(result.get('completeness', 0)):>8} "
                  f"{color_score(result.get('overall_score', 0)):>8}")


def create_html_report(data: Dict[str, Any], output_file: str):
    """HTML 리포트 생성"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>K8s Agent 평가 결과</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; }
        .metric-card { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .score-high { color: #28a745; font-weight: bold; }
        .score-medium { color: #ffc107; font-weight: bold; }
        .score-low { color: #dc3545; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .chart { margin: 20px 0; }
        .bar { height: 20px; background-color: #007bff; margin: 2px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 K8s Agent 평가 결과 리포트</h1>
"""
    
    # 메타데이터
    metadata = data.get('evaluation_metadata', data.get('metrics', {}).get('evaluation_metadata', {}))
    if metadata:
        html_content += f"""
        <div class="metric-card">
            <h2>📋 평가 정보</h2>
            <p><strong>평가 시간:</strong> {metadata.get('timestamp', 'N/A')}</p>
            <p><strong>평가 방식:</strong> {metadata.get('evaluator_used', 'N/A')}</p>
            <p><strong>Agent 품질:</strong> {metadata.get('agent_quality_level', 'N/A')}</p>
            <p><strong>테스트 케이스:</strong> {metadata.get('total_test_cases', 'N/A')}개</p>
        </div>
"""
    
    # 전체 메트릭
    metrics = data.get('metrics', {}).get('aggregate', {}).get('overall', {})
    if metrics:
        def get_score_class(score):
            if score >= 0.8: return 'score-high'
            elif score >= 0.6: return 'score-medium'
            else: return 'score-low'
        
        html_content += f"""
        <div class="metric-card">
            <h2>📊 전체 평가 결과</h2>
            <table>
                <tr>
                    <th>메트릭</th>
                    <th>평균</th>
                    <th>표준편차</th>
                    <th>최소</th>
                    <th>최대</th>
                </tr>
                <tr>
                    <td>종합 점수</td>
                    <td class="{get_score_class(metrics.get('avg_overall', 0))}">{metrics.get('avg_overall', 0):.3f}</td>
                    <td>{metrics.get('std_overall', 0):.3f}</td>
                    <td class="{get_score_class(metrics.get('min_overall', 0))}">{metrics.get('min_overall', 0):.3f}</td>
                    <td class="{get_score_class(metrics.get('max_overall', 0))}">{metrics.get('max_overall', 0):.3f}</td>
                </tr>
                <tr>
                    <td>정확성</td>
                    <td class="{get_score_class(metrics.get('avg_correctness', 0))}">{metrics.get('avg_correctness', 0):.3f}</td>
                    <td>{metrics.get('std_correctness', 0):.3f}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>관련성</td>
                    <td class="{get_score_class(metrics.get('avg_relevance', 0))}">{metrics.get('avg_relevance', 0):.3f}</td>
                    <td>{metrics.get('std_relevance', 0):.3f}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>완전성</td>
                    <td class="{get_score_class(metrics.get('avg_completeness', 0))}">{metrics.get('avg_completeness', 0):.3f}</td>
                    <td>{metrics.get('std_completeness', 0):.3f}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
            </table>
        </div>
"""
    
    # 점수 분포
    distribution = data.get('metrics', {}).get('aggregate', {}).get('distribution', {})
    if distribution:
        html_content += """
        <div class="metric-card">
            <h2>📈 점수 분포</h2>
            <div class="chart">
"""
        max_count = max(distribution.values()) if distribution.values() else 1
        for range_key, count in sorted(distribution.items()):
            width = (count / max_count) * 100
            color = '#28a745' if '0.8-1.0' in range_key else '#ffc107' if '0.6-0.8' in range_key else '#dc3545'
            html_content += f"""
                <div style="display: flex; align-items: center; margin: 5px 0;">
                    <div style="width: 80px;">{range_key}:</div>
                    <div class="bar" style="width: {width}%; background-color: {color};"></div>
                    <div style="margin-left: 10px;">{count}</div>
                </div>
"""
        html_content += """
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 HTML 리포트 생성: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='K8s Agent 평가 결과 시각화')
    parser.add_argument('json_file', help='평가 결과 JSON 파일')
    parser.add_argument('--html', help='HTML 리포트 생성', action='store_true')
    parser.add_argument('--output', help='HTML 출력 파일명', default='evaluation_report.html')
    
    args = parser.parse_args()
    
    # JSON 로드
    data = load_json_results(args.json_file)
    
    # 터미널 출력
    print(f"\n{Colors.BOLD}K8s Agent 평가 결과 분석{Colors.ENDC}")
    print(f"파일: {args.json_file}")
    
    # 각 섹션 출력
    print_metadata(data)
    print_overall_metrics(data)
    print_score_distribution(data)
    print_metrics_by_type(data)
    print_improvement_areas(data)
    print_detailed_results(data)
    
    # HTML 리포트 생성
    if args.html:
        create_html_report(data, args.output)
        print(f"\n💡 브라우저에서 열기: open {args.output}")
    
    print(f"\n✅ 분석 완료!")


if __name__ == "__main__":
    main()