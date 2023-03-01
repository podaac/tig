resource "aws_s3_bucket" "internal" {
   bucket = "${var.prefix}-internal"
   acl = "private"
}

resource "aws_s3_bucket" "public" {
   bucket = "${var.prefix}-public"
   acl = "private"
}

resource "aws_s3_bucket" "private" {
   bucket = "${var.prefix}-private"
   acl = "private"
}

resource "aws_s3_bucket" "protected" {
   bucket = "${var.prefix}-protected"
   acl = "private"
}
