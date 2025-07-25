#!/usr/bin/env python3
"""
평가 결과를 대시보드 형태로 보여주는 도구
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import glob
import os


class Dashboard:
    """평가 결과 대시보드"""
    
    def __init__(self):
        self.results_dir = "."
        self.all_results = []
    
    def load_all_results(self):
        """모든 평가 결과 파일 로드"""
        json_files = glob.glob(os.path.join(self.results_dir, "*evaluation*.json"))
        
        for file in sorted(json_files, reverse=True)[:10]:  # 최근 10개만
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['filename'] = os.path.basename(file)
                    self.all_results.append(data)
            except:
                continue
    
    def print_dashboard(self):
        """대시보드 출력"""
        self.clear_screen()
        
        print("╔" + "═" * 78 + "╗")
        print("║" + " K8s Agent 평가 대시보드 ".center(78) + "║")
        print("╠" + "═" * 78 + "╣")
        
        if not self.all_results:
            print("║" + " 평가 결과가 없습니다. ".center(78) + "║")
            print("╚" + "═" * 78 + "╝")
            return
        
        # 최근 평가 요약
        self.print_recent_evaluations()
        
        # 성능 트렌드
        self.print_performance_trend()
        
        # 쿼리 타입별 성능
        self.print_query_type_performance()
        
        print("╚" + "═" * 78 + "╝")
    
    def print_recent_evaluations(self):
        """최근 평가 목록"""
        print("║ 📋 최근 평가 결과" + " " * 61 + "║")
        print("║" + "-" * 78 + "║")
        print("║ 번호 │ 파일명                          │ Agent │ 종합점수 │ 시간     ║")
        print("║" + "-" * 78 + "║")
        
        for i, result in enumerate(self.all_results[:5], 1):
            metadata = result.get('evaluation_metadata', result.get('metrics', {}).get('evaluation_metadata', {}))
            metrics = result.get('metrics', {}).get('aggregate', {}).get('overall', {})
            
            filename = result['filename'][:30]
            agent_level = metadata.get('agent_quality_level', 'N/A')[:6]
            overall_score = metrics.get('avg_overall', 0)
            timestamp = metadata.get('timestamp', '')[:10]
            
            score_display = self.format_score(overall_score)
            
            print(f"║  {i:2d}  │ {filename:30} │ {agent_level:6} │ {score_display} │ {timestamp:10} ║")
        
        print("║" + "-" * 78 + "║")
    
    def print_performance_trend(self):
        """성능 트렌드"""
        print("║ 📈 성능 트렌드 (최근 5개)" + " " * 52 + "║")
        print("║" + "-" * 78 + "║")
        
        # 점수 추출
        scores = []
        for result in self.all_results[:5]:
            metrics = result.get('metrics', {}).get('aggregate', {}).get('overall', {})
            scores.append(metrics.get('avg_overall', 0))
        
        if scores:
            # 간단한 차트
            max_score = 1.0
            chart_width = 60
            
            for i, score in enumerate(scores):
                bar_length = int(score * chart_width)
                bar = "█" * bar_length + "░" * (chart_width - bar_length)
                print(f"║ {i+1} │ {bar} │ {score:.3f} ║")
        
        print("║" + "-" * 78 + "║")
    
    def print_query_type_performance(self):
        """쿼리 타입별 성능"""
        if not self.all_results:
            return
            
        latest = self.all_results[0]
        by_type = latest.get('metrics', {}).get('by_query_type', {})
        
        if by_type:
            print("║ 🔍 쿼리 타입별 성능 (최신)" + " " * 51 + "║")
            print("║" + "-" * 78 + "║")
            print("║ 타입               │ 정확성 │ 관련성 │ 완전성 │ 종합   │ 건수 ║")
            print("║" + "-" * 78 + "║")
            
            for query_type, metrics in sorted(by_type.items()):
                print(f"║ {query_type:18} │ "
                      f"{self.format_score_short(metrics.get('avg_correctness', 0))} │ "
                      f"{self.format_score_short(metrics.get('avg_relevance', 0))} │ "
                      f"{self.format_score_short(metrics.get('avg_completeness', 0))} │ "
                      f"{self.format_score_short(metrics.get('avg_overall', 0))} │ "
                      f"{metrics.get('count', 0):4d} ║")
            
            print("║" + "-" * 78 + "║")
    
    def format_score(self, score):
        """점수 포맷팅 (색상 없이)"""
        if score >= 0.8:
            return f"{score:6.3f} 🟢"
        elif score >= 0.6:
            return f"{score:6.3f} 🟡"
        else:
            return f"{score:6.3f} 🔴"
    
    def format_score_short(self, score):
        """짧은 점수 포맷팅"""
        if score >= 0.8:
            return f"{score:.3f}"
        elif score >= 0.6:
            return f"{score:.3f}"
        else:
            return f"{score:.3f}"
    
    def clear_screen(self):
        """화면 지우기"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def run_interactive(self):
        """대화형 모드"""
        while True:
            self.load_all_results()
            self.print_dashboard()
            
            print("\n옵션: [R]새로고침 [1-5]상세보기 [Q]종료")
            choice = input("선택: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'r':
                continue
            elif choice.isdigit() and 1 <= int(choice) <= min(5, len(self.all_results)):
                self.show_details(int(choice) - 1)
            else:
                print("잘못된 선택입니다.")
                input("계속하려면 Enter...")
    
    def show_details(self, index):
        """상세 정보 표시"""
        result = self.all_results[index]
        
        self.clear_screen()
        print("╔" + "═" * 78 + "╗")
        print("║" + f" 상세 평가 결과: {result['filename']} ".center(78) + "║")
        print("╠" + "═" * 78 + "╣")
        
        # 메타데이터
        metadata = result.get('evaluation_metadata', result.get('metrics', {}).get('evaluation_metadata', {}))
        print("║ 📋 평가 정보" + " " * 65 + "║")
        print("║" + "-" * 78 + "║")
        print(f"║ 평가 시간: {metadata.get('timestamp', 'N/A'):66} ║")
        print(f"║ 평가 방식: {metadata.get('evaluator_used', 'N/A'):66} ║")
        print(f"║ Agent 품질: {metadata.get('agent_quality_level', 'N/A'):65} ║")
        print(f"║ 테스트 케이스: {str(metadata.get('total_test_cases', 'N/A')) + '개':62} ║")
        
        # 전체 메트릭
        metrics = result.get('metrics', {}).get('aggregate', {}).get('overall', {})
        if metrics:
            print("║" + "-" * 78 + "║")
            print("║ 📊 전체 평가 결과" + " " * 60 + "║")
            print("║" + "-" * 78 + "║")
            print(f"║ 종합 점수: {self.format_score(metrics.get('avg_overall', 0)):>66} ║")
            print(f"║ 정확성:   {self.format_score(metrics.get('avg_correctness', 0)):>67} ║")
            print(f"║ 관련성:   {self.format_score(metrics.get('avg_relevance', 0)):>67} ║")
            print(f"║ 완전성:   {self.format_score(metrics.get('avg_completeness', 0)):>67} ║")
        
        # 개선 영역
        improvement = result.get('metrics', {}).get('improvement_areas', {})
        if improvement:
            print("║" + "-" * 78 + "║")
            print("║ 🎯 개선 필요 영역" + " " * 60 + "║")
            print("║" + "-" * 78 + "║")
            print(f"║ 낮은 성능 케이스: {improvement.get('low_performing_count', 0)}개 ({improvement.get('low_performing_percentage', 0):.1f}%)" + " " * 46 + "║")
            print(f"║ 주요 문제: {improvement.get('most_common_issue', 'N/A'):65} ║")
        
        print("╚" + "═" * 78 + "╝")
        
        input("\n계속하려면 Enter...")


def compare_results(file1: str, file2: str):
    """두 평가 결과 비교"""
    try:
        with open(file1, 'r') as f:
            data1 = json.load(f)
        with open(file2, 'r') as f:
            data2 = json.load(f)
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return
    
    print("\n" + "=" * 80)
    print("평가 결과 비교".center(80))
    print("=" * 80)
    
    # 메타데이터 비교
    meta1 = data1.get('evaluation_metadata', data1.get('metrics', {}).get('evaluation_metadata', {}))
    meta2 = data2.get('evaluation_metadata', data2.get('metrics', {}).get('evaluation_metadata', {}))
    
    print(f"\n{'':20} {'파일 1':^25} │ {'파일 2':^25}")
    print("-" * 80)
    print(f"{'Agent 품질':20} {meta1.get('agent_quality_level', 'N/A'):^25} │ {meta2.get('agent_quality_level', 'N/A'):^25}")
    print(f"{'테스트 케이스':20} {str(meta1.get('total_test_cases', 'N/A')):^25} │ {str(meta2.get('total_test_cases', 'N/A')):^25}")
    
    # 메트릭 비교
    metrics1 = data1.get('metrics', {}).get('aggregate', {}).get('overall', {})
    metrics2 = data2.get('metrics', {}).get('aggregate', {}).get('overall', {})
    
    print("\n전체 성능 비교:")
    print("-" * 80)
    
    for metric in ['avg_overall', 'avg_correctness', 'avg_relevance', 'avg_completeness']:
        val1 = metrics1.get(metric, 0)
        val2 = metrics2.get(metric, 0)
        diff = val2 - val1
        
        metric_name = metric.replace('avg_', '').replace('_', ' ').title()
        
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "="
        color_diff = f"+{diff:.3f}" if diff > 0 else f"{diff:.3f}"
        
        print(f"{metric_name:20} {val1:^25.3f} │ {val2:^25.3f} │ {arrow} {color_diff}")
    
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--compare" and len(sys.argv) >= 4:
            # 비교 모드
            compare_results(sys.argv[2], sys.argv[3])
        else:
            # 단일 파일 분석
            from visualize_results import main as visualize_main
            sys.argv = ['visualize_results.py'] + sys.argv[1:]
            visualize_main()
    else:
        # 대시보드 모드
        dashboard = Dashboard()
        dashboard.run_interactive()