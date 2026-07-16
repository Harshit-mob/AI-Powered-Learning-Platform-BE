from collections import defaultdict

class GenerationReporter:
    def __init__(self):
        self.lu_stats = defaultdict(lambda: {
            "title": "",
            "Generated": 0,
            "Accepted": 0,
            "Rejected": 0,
            "Duplicates": 0,
            "Warnings": 0,
            "Coverage": 0.0,
            "Quality": 0.0,
            "Voice": 0.0,
            "rejections_reasons": defaultdict(int)
        })
        self.chapter_stats = {
            "Generated": 0,
            "Accepted": 0,
            "Rejected": 0,
            "Duplicates": 0,
            "Processing_Time": 0.0
        }
        self.rejection_analytics = defaultdict(int)

    def record_lu_stats(self, unit_id: str, title: str, stats: dict):
        self.lu_stats[unit_id].update(stats)
        self.lu_stats[unit_id]["title"] = title
        
        self.chapter_stats["Generated"] += stats.get("Generated", 0)
        self.chapter_stats["Accepted"] += stats.get("Accepted", 0)
        self.chapter_stats["Rejected"] += stats.get("Rejected", 0)
        self.chapter_stats["Duplicates"] += stats.get("Duplicates", 0)
        
        for reason, count in stats.get("rejections_reasons", {}).items():
            self.rejection_analytics[reason] += count

    def generate_lu_report(self, unit_id: str) -> str:
        s = self.lu_stats[unit_id]
        report = []
        report.append("=====================================")
        report.append("Learning Unit")
        report.append(s["title"])
        report.append("Generated")
        report.append(str(s["Generated"]))
        report.append("Accepted")
        report.append(str(s["Accepted"]))
        report.append("Rejected")
        report.append(str(s["Rejected"]))
        report.append("Coverage")
        report.append(f"{s['Coverage']:.0f}%")
        report.append("Voice")
        report.append(f"{s['Voice']:.0f}%")
        report.append("Quality")
        report.append(f"{s['Quality']:.0f}%")
        report.append("Duplicates")
        report.append(str(s["Duplicates"]))
        report.append("Warnings")
        report.append(str(s["Warnings"]))
        report.append("Status")
        report.append("READY")
        report.append("=====================================")
        return "\n".join(report)

    def generate_chapter_report(self, chapter_title: str, processing_time: float) -> str:
        total_units = len(self.lu_stats)
        avg_cov = sum(s["Coverage"] for s in self.lu_stats.values()) / total_units if total_units > 0 else 0
        avg_qual = sum(s["Quality"] for s in self.lu_stats.values()) / total_units if total_units > 0 else 0
        avg_voice = sum(s["Voice"] for s in self.lu_stats.values()) / total_units if total_units > 0 else 0
        
        report = []
        report.append("=====================================")
        report.append("Chapter")
        report.append(chapter_title)
        report.append("Learning Units")
        report.append(str(total_units))
        report.append("Questions Generated")
        report.append(str(self.chapter_stats["Generated"]))
        report.append("Accepted")
        report.append(str(self.chapter_stats["Accepted"]))
        report.append("Rejected")
        report.append(str(self.chapter_stats["Rejected"]))
        report.append("Coverage")
        report.append(f"{avg_cov:.0f}%")
        report.append("Quality")
        report.append(f"{avg_qual:.0f}%")
        report.append("Voice")
        report.append(f"{avg_voice:.0f}%")
        report.append("Duplicates")
        report.append(str(self.chapter_stats["Duplicates"]))
        report.append("Processing Time")
        report.append(f"{processing_time:.0f} sec")
        report.append("Status")
        report.append("READY")
        report.append("=====================================")
        
        if self.rejection_analytics:
            report.append("\nRejected")
            for reason, count in sorted(self.rejection_analytics.items(), key=lambda x: x[1], reverse=True):
                report.append(f"{reason}\n{count}")
                
        return "\n".join(report)
