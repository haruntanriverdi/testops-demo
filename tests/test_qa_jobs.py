import time
import logging
from pages import CareersPage, OpenPositionsPage

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class TestQAJobs:

    def test_qa_jobs_istanbul(self, driver):
        log.info("Starting test: QA jobs filter")

        careers = CareersPage(driver)
        careers.open()
        assert careers.is_loaded()
        log.info("Careers page loaded")

        careers.click_see_all_jobs()

        positions = OpenPositionsPage(driver)
        positions.wait_ready()
        positions.select_location("Istanbul, Turkiye")
        positions.select_department("Quality Assurance")
        log.info("Filters applied")

        jobs = positions.get_jobs()
        assert len(jobs) > 0, "No jobs found"
        log.info(f"Found {len(jobs)} job(s)")

        for job in jobs:
            info = positions.get_job_info(job)
            log.info(f"  -> {info['position']} | {info['department']} | {info['location']}")
            assert "quality" in info["position"].lower()
            assert "quality assurance" in info["department"].lower()
            assert "istanbul, turkiye" in info["location"].lower()

        positions.click_view_role(jobs[0])
        time.sleep(1)
        positions.switch_to_new_tab()

        assert "lever.co" in positions.current_url()
        log.info("Redirected to Lever - OK")
