module "galaxy" {
  #source   = "github.com/brinkmanlab/galaxy-container.git//destinations/docker"
  source   = "../../../galaxy-container/destinations/docker"
  instance = var.instance
  galaxy_conf = {
    email_from     = var.email
    error_email_to = var.email
    require_login  = true
    #allow_user_creation = false
    #cleanup_job = "never"
    slow_query_log_threshold = 500
  }
  image_tag   = "dev"
  admin_users = [var.email]
  email       = var.email
  debug       = var.debug
  tool_mappings = {
    "progressivemauve": "c1m2"
    "rgi": "c4m8"
    "tp_awk_tool": "tiny"
    "tp_text_file_with_recurring_lines": "tiny"
    "sigihmm": "c4m8"
    "feature-merge": "c1m8"
    "islandpath": "c1m2"
    "mash": "c4m8"
    "parsnp": "c16m32"
    "mcl": "c4m8"
    "biopython-convert": "c1m2"
    "extract-tree-order": "tiny"
    "mauve-contig-mover": "c1m2"
    "mauve-contig-mover-stitch": "c1m1"
    "make-unique-id": "tiny"
    "sendmail": "local-tiny"
    "sha256sum": "tiny"
    "awkscript": "tiny"
  }
  #extra_mounts = [
  #  {
  #    target = "/cvmfs/microbedb.brinkmanlab.ca"
  #    source = "${abspath(var.microbedb_mount_path)}/datasets/"
  #    type = "bind"
  #    read_only = true
  #  }
  #]
  extra_job_mounts = ["${abspath(var.microbedb_mount_path)}/dataset/:/cvmfs/microbedb.brinkmanlab.ca:ro"]
  host_port = var.host_port
  docker_gid = var.docker_gid
}

module "admin_user" {
  source         = "github.com/brinkmanlab/galaxy-container.git//modules/bootstrap_admin"
  email          = var.email
  galaxy_url     = "http://localhost:${module.galaxy.host_port}"
  master_api_key = module.galaxy.master_api_key
  username       = "admin"
}

provider "galaxy" {
  host   = "http://localhost:${module.galaxy.host_port}"
  apikey = module.admin_user.api_key
}

module "islandcompare" {
  source                = "github.com/brinkmanlab/IslandCompare.git//destinations/docker"
  instance              = var.instance
  data_dir              = module.galaxy.data_dir
  debug = var.debug
  microbedb_mount_path = abspath(var.microbedb_mount_path)
}

resource "local_file" "env" {
  filename = "env.sh"
  content = <<-EOF
  export GALAXY_HOST='http://localhost:${var.host_port}'
  export GALAXY_API_KEY='${module.admin_user.api_key}'
  EOF
}